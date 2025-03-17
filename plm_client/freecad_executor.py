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


class FreeCADExecutor:
    """
    Класс для выполнения Python-кода в интерпретаторе FreeCAD.
    Предоставляет безопасное окружение для выполнения кода и доступ к API FreeCAD.
    """
    
    def __init__(self, logger_callback: Callable[[str], None] = None):
        """
        Инициализирует исполнитель кода FreeCAD.
        
        Args:
            logger_callback: Функция обратного вызова для логирования сообщений
        """
        self.logger = logger_callback or print
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
            self.logger("FreeCAD успешно импортирован")
        except ImportError:
            self.freecad_available = False
            self.logger("Предупреждение: FreeCAD не найден. Некоторые функции могут быть недоступны.")
            
        # Добавляем путь к PLMplugin в sys.path, если его там нет
        try:
            # Определяем путь к PLMplugin относительно текущего файла
            current_dir = os.path.dirname(os.path.abspath(__file__))
            plugin_path = os.path.join(os.path.dirname(current_dir), 'PLMplugin')
            
            if os.path.exists(plugin_path) and plugin_path not in sys.path:
                sys.path.append(plugin_path)
                self.logger(f"Добавлен путь к PLMplugin: {plugin_path}")
        except Exception as e:
            self.logger(f"Ошибка при настройке путей: {str(e)}")
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        Выполняет Python-код в интерпретаторе FreeCAD.
        
        Args:
            code: Python-код для выполнения
            
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
            return {
                'success': False,
                'message': 'FreeCAD не доступен',
                'error': 'Не удалось импортировать FreeCAD. Убедитесь, что FreeCAD установлен и доступен.'
            }
            
        try:
            self.logger("Выполнение Python-кода...")
            
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
                from cad_utils import CADUtils, Coordinates, PartCreationDTO
                local_vars['CADUtils'] = CADUtils
                local_vars['Coordinates'] = Coordinates
                local_vars['PartCreationDTO'] = PartCreationDTO
            except ImportError as e:
                self.logger(f"Предупреждение: Не удалось импортировать CADUtils: {str(e)}")
                
            # Выполняем код
            result = {}
            exec(code, globals(), local_vars)
            
            # Проверяем, был ли создан результат в локальных переменных
            if 'result' in local_vars:
                result = local_vars['result']
                
            return {
                'success': True,
                'message': 'Python-код успешно выполнен',
                'result': result
            }
                
        except Exception as e:
            error_msg = f"Ошибка при выполнении Python-кода: {str(e)}\n{traceback.format_exc()}"
            self.logger(error_msg)
            return {
                'success': False,
                'message': 'Ошибка при выполнении кода',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def execute_simple_command(self, command: str) -> Dict[str, Any]:
        """
        Выполняет простую команду FreeCAD.
        Это обертка для execute_code, которая обрабатывает простые команды.
        
        Args:
            command: Строка с командой
            
        Returns:
            Словарь с результатами выполнения
        """
        # Настраиваем окружение при первом использовании
        self._setup_environment()
        
        # Добавляем отладочное сообщение
        self.logger(f"Выполнение простой команды: {command}")
        
        # Проверяем, является ли команда простой командой печати
        if command.strip().startswith('print('):
            try:
                # Добавляем отладочное сообщение
                self.logger("Обнаружена команда print(), перехватываем вывод")
                
                # Выполняем команду print и перехватываем вывод
                import io
                import sys
                original_stdout = sys.stdout
                captured_output = io.StringIO()
                sys.stdout = captured_output
                
                # Выполняем код
                exec(command)
                
                # Восстанавливаем stdout и получаем вывод
                sys.stdout = original_stdout
                output = captured_output.getvalue().strip()
                
                # Добавляем отладочное сообщение
                self.logger(f"Результат выполнения print(): {output}")
                
                return {
                    'success': True,
                    'message': f'Команда выполнена: {command}',
                    'result': output
                }
            except Exception as e:
                # Добавляем отладочное сообщение
                self.logger(f"Ошибка при выполнении print(): {str(e)}")
                
                return {
                    'success': False,
                    'message': f'Ошибка при выполнении команды: {command}',
                    'error': str(e)
                }
        
        # Добавляем отладочное сообщение
        self.logger("Используем обычный execute_code для выполнения команды")
        
        # Для других команд используем обычный execute_code
        return self.execute_code(command)


# Пример использования
if __name__ == "__main__":
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