from typing import Optional
import json
from mcp.server.fastmcp import FastMCP
import traceback
import socket
from consts import FREECAD_HOST, FREECAD_PORT

# Инициализация FastMCP сервера
mcp = FastMCP("freecad_plm")

async def send_to_freecad(command: dict) -> dict:
    """Отправляет команду в FreeCAD и получает ответ."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((FREECAD_HOST, FREECAD_PORT))
        command_json = json.dumps(command)
        sock.sendall(command_json.encode('utf-8'))
        response = sock.recv(32768)
        sock.close()
        return json.loads(response.decode('utf-8'))
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def run_script(script: str, result: Optional[str] = None) -> str:
    """Выполняет Python-скрипт в контексте FreeCAD.
    
    Args:
        script: Python-скрипт для выполнения в FreeCAD.
        result: Опциональное имя переменной для результата. Если указано, будет добавлено в конец скрипта.
               Например, при значении "{{'document_name': doc.Name}}" будет добавлено "result = {'document_name': real_document_name}"
    
    Returns:
        JSON-строка, содержащая результат выполнения
    """
    try:
        # Если указан result_var, добавляем его в конец скрипта
        if result:
            full_script = f"{script}\nresult = {result}"
        else:
            full_script = script
            
        # Отправляем скрипт через сокет
        command = {
            "type": "run_script",
            "params": {
                "script": full_script
            }
        }
        
        result = await send_to_freecad(command)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            'success': False,
            'message': 'Ошибка при выполнении скрипта',
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return json.dumps(error_result, indent=2)

@mcp.tool()
async def capture_part_view(part_name: str, view_type: str) -> str:
    """Делает скриншот детали и сохраняет его в файл.
    
    Args:
        part_name: Название (Label) детали для отображения.
        view_type: Тип вида: 'front', 'top', 'right', 'left', 'rear', 'bottom', 'isometric'.
    
    Returns:
        JSON-строка, содержащая результат выполнения с полем image_data, которое содержит
        строку base64 с данными изображения в формате PNG.
    """
    try:
        # Отправляем команду через сокет
        command = {
            "type": "capture_part_view",
            "params": {
                "part_name": part_name,
                "view_type": view_type
            }
        }
        
        result = await send_to_freecad(command)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            'success': False,
            'message': 'Ошибка при получении скриншота детали',
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return json.dumps(error_result, indent=2)

@mcp.tool()
async def compare_objects(obj1_name: str, obj2_name: str, tolerance: float = 1e-6) -> str:
    """Сравнивает два объекта FreeCAD на идентичность их геометрии.
    
    Args:
        obj1_name: Имя первого объекта для сравнения.
        obj2_name: Имя второго объекта для сравнения.
        tolerance: Допустимая погрешность при сравнении (по умолчанию 1e-6).
    
    Returns:
        JSON-строка, содержащая результат сравнения.
    """
    try:
        script = f"""
import FreeCAD as App
from utils.cad_utils import CADUtils

try:
    if not App.ActiveDocument:
        raise Exception("Нет активного документа. Перед сравнением объектов нужно создать или открыть документ.")
    identical = CADUtils.object_are_identical("{obj1_name}", "{obj2_name}", {tolerance})
    result = {{"success": True, "identical": identical}}
except Exception as e:
    import traceback
    result = {{"success": False, "error": str(e), "traceback": traceback.format_exc()}}
"""
        
        # Отправляем скрипт через сокет
        command = {
            "type": "run_script",
            "params": {
                "script": script
            }
        }
        
        result = await send_to_freecad(command)
        return json.dumps(result, indent=2)
        
    except Exception as e:
        error_result = {
            'success': False,
            'message': 'Ошибка при сравнении объектов',
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return json.dumps(error_result, indent=2)


if __name__ == "__main__":
    # Инициализация и запуск сервера
    mcp.run(transport='stdio') 