from typing import Optional
import json
from mcp.server.fastmcp import FastMCP
from freecad_executor import FreeCADExecutor
import traceback

mcp = FastMCP("freecad_plm")

executor = FreeCADExecutor()

@mcp.tool()
async def run_script(script: str, result_var: Optional[str] = None) -> str:
    """Выполняет Python-скрипт в контексте FreeCAD.
    
    Args:
        script: Python-скрипт для выполнения в FreeCAD. Для возврата результата в конце скрипта
               добавьте строку вида: result = {'object_created': part_obj.Name, 'document_name': doc.Name}
        result_var: Опциональное имя переменной для результата. Если указано, будет добавлено в конец скрипта.
               Например, при значении "{'success': True}" будет добавлено "result = {'success': True}"
    
    Returns:
        JSON-строка, содержащая результат выполнения
    """
    try:
        # Если указан result_var, добавляем его в конец скрипта
        if result_var:
            full_script = f"{script}\nresult = {result_var}"
        else:
            full_script = script
            
        # Выполняем скрипт
        result = executor.execute_code(full_script, send_result=False)
        return json.dumps(result, indent=2)
    except Exception as e:
        error_result = {
            'success': False,
            'message': 'Ошибка при выполнении скрипта',
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        return json.dumps(error_result, indent=2)

if __name__ == "__main__":
    # Инициализация и запуск сервера
    mcp.run(transport='stdio') 