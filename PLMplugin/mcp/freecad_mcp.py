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

if __name__ == "__main__":
    # Инициализация и запуск сервера
    mcp.run(transport='stdio') 