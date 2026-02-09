# Выполнение Python-кода в FreeCAD через PLM-клиент

## Обзор

Данная функциональность позволяет выполнять Python-код, полученный от сервера, в интерпретаторе FreeCAD для манипуляций с CAD-моделями. Это позволяет удаленно управлять FreeCAD и выполнять различные операции с моделями.

## Форматы сообщений

Сервер может отправлять сообщения в следующих форматах:

### 1. JSON с полем python_code

```json
{
  "python_code": "import FreeCAD\nimport Part\n\ndoc = FreeCAD.newDocument('Example')\nbox = Part.makeBox(10, 10, 10)\ncube = doc.addObject('Part::Feature', 'Cube')\ncube.Shape = box\ndoc.recompute()"
}
```

### 2. Сообщение с префиксом EXEC_PYTHON:

```
EXEC_PYTHON:import FreeCAD
doc = FreeCAD.newDocument('Example')
# ... остальной код ...
```

### 3. Простые команды Python

Клиент также распознает и выполняет простые команды Python, такие как:

```
print('hello')
```

```
FreeCAD.newDocument('Test')
```

Простые команды (длиной менее 50 символов) выполняются автоматически, без запроса подтверждения.

## Примеры использования

### Создание куба

```json
{
  "python_code": "
import FreeCAD
import Part

doc = FreeCAD.newDocument('Example')
box = Part.makeBox(10, 10, 10)
cube = doc.addObject('Part::Feature', 'Cube')
cube.Shape = box
doc.recompute()

# Возвращаем результат
result = {'object_created': cube.Name, 'dimensions': [10, 10, 10]}
"
}
```

### Открытие файла

```json
{
  "python_code": "
import FreeCAD
FreeCAD.open('/path/to/model.fcstd')
"
}
```

### Сохранение файла

```json
{
  "python_code": "
import FreeCAD
import Part

doc = FreeCAD.ActiveDocument
if doc:
    # Сохранение в формате FCSTD
    doc.saveAs('/path/to/output.fcstd')
    
    # Или экспорт в STEP
    Part.export(doc.Objects, '/path/to/output.step')
"
}
```

### Выполнение простой команды

```
print('Hello from FreeCAD!')
```

## Безопасность

При получении Python-кода от сервера клиент может:

1. Автоматически выполнить код, если он получен в структурированном формате (JSON с полем python_code или с префиксом EXEC_PYTHON:)
2. Автоматически выполнить простые команды (длиной менее 50 символов)
3. Запросить подтверждение у пользователя, если код получен в неструктурированном формате и не является простой командой

## Архитектура

Функциональность реализована в следующих файлах:

1. `plm_client/freecad_executor.py` - основной класс для выполнения Python-кода в FreeCAD
2. `plm_client/client_window.py` - интеграция с пользовательским интерфейсом

## Требования

- FreeCAD (проверено на версии 0.19 и выше)
- Python 3.6+
- PySide2 или PyQt5

## Ограничения

- Код выполняется в контексте текущего процесса FreeCAD
- Некоторые операции могут требовать перезагрузки FreeCAD
- Выполнение вредоносного кода может повредить систему пользователя

## Отправка результатов через WebSocket

Класс `FreeCADExecutor` теперь поддерживает отправку результатов выполнения кода на сервер через WebSocket. Для использования этой функциональности:

1. Инициализируйте `FreeCADExecutor` с функцией обратного вызова `websocket_sender`:

```python
def websocket_sender(data):
    # Преобразуем данные в JSON
    json_data = json.dumps(data)
    # Отправляем через веб-сокет
    send_message(json_data)

executor = FreeCADExecutor(
    logger_callback=print,
    websocket_sender=websocket_sender
)
```

2. Используйте параметр `send_result=True` при вызове методов `execute_code` или `execute_simple_command`:

```python
result = executor.execute_code(code, send_result=True)
```

3. Структура отправляемых данных:

```json
{
    "type": "execution_result",
    "data": {
        "success": true,
        "message": "Python-код успешно выполнен",
        "result": { ... } // Результат выполнения кода
    }
}
```

4. Пример интеграции с клиентом WebSocket:

```python
from plm_client.freecad_executor import FreeCADExecutor
from plm_client.socket_client import create_websocket_client

# Создаем WebSocket клиент
send_message, receive_message, close_connection = create_websocket_client('localhost', 8765)

# Функция для отправки результатов через WebSocket
def websocket_sender(data):
    json_data = json.dumps(data)
    send_message(json_data)

# Инициализируем executor с настроенной функцией отправки
executor = FreeCADExecutor(
    logger_callback=print,
    websocket_sender=websocket_sender
)

# Выполняем код с отправкой результата на сервер
executor.execute_code("result = {'message': 'Hello from FreeCAD!'}", send_result=True)
``` 