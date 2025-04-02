"""
Модуль для выполнения Python-кода в интерпретаторе FreeCAD.
Предоставляет функции для безопасного выполнения кода и манипуляций с CAD-моделями.
"""

import traceback
import sys
import os
import importlib
import json
from typing import Dict, Any, Callable
from utils.logger import log


class FreeCADExecutor:
    """
    Класс для выполнения Python-кода в интерпретаторе FreeCAD.
    Предоставляет безопасное окружение для выполнения кода и доступ к API FreeCAD.
    """
    
    def __init__(self, websocket_sender: Callable[[Dict[str, Any]], None] = None):
        """
        Инициализирует исполнитель кода FreeCAD.
        
        Args:
            logger_callback: Функция обратного вызова для логирования сообщений
            websocket_sender: Функция для отправки сообщений через веб-сокет
        """
        
        self.websocket_sender = websocket_sender
        # Откладываем настройку окружения до первого использования
        self.freecad_available = None
        
    def _setup_environment(self) -> None:
        """Настраивает окружение для выполнения кода FreeCAD"""
        # Если окружение уже настроено, не делаем ничего
        if self.freecad_available is not None:
            return
            
        # Проверяем, доступен ли FreeCAD
        try:
            import FreeCAD
            import FreeCADGui
            self.freecad_available = True
            
            log("FreeCAD успешно импортирован")
        except ImportError:
            self.freecad_available = False
            
            log("Предупреждение: FreeCAD не найден")
            
        # Добавляем путь к PLMplugin в sys.path, если его там нет
        try:
            # Определяем путь к PLMplugin относительно текущего файла
            current_dir = os.path.dirname(os.path.abspath(__file__))
            plugin_path = os.path.join(os.path.dirname(current_dir), 'PLMplugin')
            
            if os.path.exists(plugin_path) and plugin_path not in sys.path:
                sys.path.append(plugin_path)
                
                log(f"Добавлен путь к PLMplugin: {plugin_path}")
        except Exception as e:
            
            log(f"Ошибка при настройке путей: {str(e)}")
    
    def execute_code(self, code: str, send_result: bool = False) -> Dict[str, Any]:
        """
        Выполняет Python-код в интерпретаторе FreeCAD.
        
        Args:
            code: Python-код для выполнения
            send_result: Отправлять ли результат через веб-сокет
            
        Returns:
            Словарь с результатами выполнения:
                - success: Успешно ли выполнен код
                - message: Сообщение о результате
                - error: Сообщение об ошибке (если есть)
                - result: Результат выполнения (если есть)
        """
        # Настраиваем окружение при первом использовании
        self._setup_environment()
        
        if not self.freecad_available:
            result = {
                'success': False,
                'message': 'FreeCAD не доступен',
                'error': 'Не удалось импортировать FreeCAD. Убедитесь, что FreeCAD установлен и доступен.'
            }
            if send_result and self.websocket_sender:
                self.send_result_via_websocket(result)
            return result
            
        try:
            log("Выполнение Python-кода...")
            
            # Импортируем необходимые модули FreeCAD
            import FreeCAD
            import FreeCADGui
            
            # Создаем локальный словарь для выполнения кода
            local_vars = {
                'FreeCAD': FreeCAD,
                'Gui': FreeCADGui,
                'App': FreeCAD,  # Алиас для совместимости
            }
            
            # Пытаемся импортировать другие модули FreeCAD
            modules_to_import = ['Part', 'Draft', 'Mesh', 'Sketcher', 'PartDesign']
            for module_name in modules_to_import:
                try:
                    module = importlib.import_module(module_name)
                    local_vars[module_name] = module
                except ImportError:
                    pass
                    
            # Добавляем утилиты CAD, если они доступны
            try:
                from utils.cad_utils import CADUtils, Coordinates, PartCreationDTO
                local_vars['CADUtils'] = CADUtils
                local_vars['Coordinates'] = Coordinates
                local_vars['PartCreationDTO'] = PartCreationDTO
            except ImportError as e:
                log(f"Предупреждение: Не удалось импортировать CADUtils: {str(e)}")
                
            # Выполняем код
            result = {}
            exec(code, globals(), local_vars)
            
            # Проверяем, был ли создан результат в локальных переменных
            if 'result' in local_vars:
                result = local_vars['result']
                
            result_dict = {
                'success': True,
                'message': 'Python-код успешно выполнен',
                'result': result
            }
            
            # Отправляем результат через веб-сокет, если это требуется
            if send_result and self.websocket_sender:
                self.send_result_via_websocket(result_dict)
                
            return result_dict
                
        except Exception as e:
            error_msg = f"Ошибка при выполнении Python-кода: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            
            result_dict = {
                'success': False,
                'message': 'Ошибка при выполнении кода',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            
            # Отправляем сообщение об ошибке через веб-сокет, если это требуется
            if send_result and self.websocket_sender:
                self.send_result_via_websocket(result_dict)
                
            return result_dict
        
    def send_result_via_websocket(self, result: Dict[str, Any]) -> None:
        """
        Отправляет результат выполнения кода через веб-сокет.
        
        Args:
            result: Словарь с результатами выполнения
        """
        if not self.websocket_sender:
            log("Предупреждение: Не настроен обработчик веб-сокета для отправки результатов")
            return
            
        try:
            # Преобразуем результат в JSON
            json_result = json.dumps(result)
            
            # Добавляем метку для идентификации типа сообщения
            data_to_send = {
                'type': 'execution_result',
                'data': result
            }
            
            # Отправляем через веб-сокет
            self.websocket_sender(data_to_send)
            log("Результат успешно отправлен через веб-сокет")
        except Exception as e:
            log(f"Ошибка при отправке результата через веб-сокет: {str(e)}")


# Пример использования
if __name__ == "__main__":
    # Для отладки
    from logger import debug
    debug = True  # Включаем отладку только для прямого запуска модуля
    
    executor = FreeCADExecutor()
    
    # Пример выполнения простого кода
    result = executor.execute_code("""
import FreeCAD
import Part

# Создаем новый документ
doc = FreeCAD.newDocument("Example")

# Создаем куб
box = Part.makeBox(10, 10, 10)
cube = doc.addObject("Part::Feature", "Cube")
cube.Shape = box

# Перерасчитываем документ
doc.recompute()

# Возвращаем результат
result = {"object_created": cube.Name, "dimensions": [10, 10, 10]}
""")
    
    print(json.dumps(result, indent=2)) 