import json
import threading
import time
from plm_functions import PLMFunctions
from PySide2 import QtWidgets, QtCore

from socket_client import create_websocket_client
import traceback
from freecad_executor import FreeCADExecutor
from logger import log
from function_registry import FunctionRegistry

class PLMClientPanel(QtWidgets.QWidget):
    # Сигнал для обновления UI из другого потока
    message_received = QtCore.Signal(str)
    connection_status_changed = QtCore.Signal(bool, str)
    # Добавляем сигнал для выполнения кода в главном потоке
    execute_code_signal = QtCore.Signal(str)
    # Добавляем сигнал для выполнения функций в главном потоке
    execute_function_signal = QtCore.Signal(str, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.send_message = None
        self.receive_message = None
        self.close_connection = None
        self.listener_thread = None
        self.is_connected = False
        
        self.freecad_executor = FreeCADExecutor()
        self.function_registry = FunctionRegistry()  # Создаем экземпляр реестра функций
        
        # Переменная для хранения PLMFunctions
        self.plm_functions = None
        
        self.setup_ui()
        
        # Подключаем сигналы
        self.message_received.connect(self.update_messages)
        self.connection_status_changed.connect(self.update_connection_status)
        # Подключаем сигнал для выполнения кода
        self.execute_code_signal.connect(self.execute_code_in_main_thread)
        # Подключаем сигнал для выполнения функций
        self.execute_function_signal.connect(self.execute_function_in_main_thread)

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Область настроек соединения
        connection_layout = QtWidgets.QGridLayout()
        
        # Поле для хоста
        self.host_label = QtWidgets.QLabel('Хост:')
        self.host_input = QtWidgets.QLineEdit('localhost')
        connection_layout.addWidget(self.host_label, 0, 0)
        connection_layout.addWidget(self.host_input, 0, 1)
        
        # Поле для порта
        self.port_label = QtWidgets.QLabel('Порт:')
        self.port_input = QtWidgets.QLineEdit('8765')
        connection_layout.addWidget(self.port_label, 1, 0)
        connection_layout.addWidget(self.port_input, 1, 1)
        
        # Кнопка подключения
        self.connect_button = QtWidgets.QPushButton('Подключиться')
        self.connect_button.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.connect_button, 2, 0, 1, 2)
        
        # Статус соединения
        self.status_label = QtWidgets.QLabel('Статус: Отключено')
        connection_layout.addWidget(self.status_label, 3, 0, 1, 2)
        
        layout.addLayout(connection_layout)
        
        # Область для отправки сообщений
        message_layout = QtWidgets.QHBoxLayout()
        self.message_input = QtWidgets.QLineEdit()
        self.message_input.setPlaceholderText('Введите сообщение...')
        self.message_input.setEnabled(False)
        # Добавляем обработку нажатия Enter для отправки сообщения
        self.message_input.returnPressed.connect(self.send_message_to_server)
        
        self.send_button = QtWidgets.QPushButton('Отправить')
        self.send_button.clicked.connect(self.send_message_to_server)
        self.send_button.setEnabled(False)
        
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.send_button)
        
        layout.addLayout(message_layout)
        
        # Область для отображения сообщений
        self.messages_display = QtWidgets.QTextEdit()
        self.messages_display.setReadOnly(True)
        layout.addWidget(self.messages_display)
        
        # Кнопка очистки сообщений
        self.clear_button = QtWidgets.QPushButton('Очистить сообщения')
        self.clear_button.clicked.connect(self.clear_messages)
        layout.addWidget(self.clear_button)

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()

    def connect_to_server(self):
        host = self.host_input.text()
        try:
            port = int(self.port_input.text())
        except ValueError:
            self.add_message("Ошибка: Порт должен быть числом")
            return
            
        try:
            self.add_message(f"Подключение к {host}:{port}...")
            self.send_message, self.receive_message, self.close_connection = create_websocket_client(host, port)
            
            # Проверяем, что функции получены корректно
            if not self.send_message or not self.receive_message or not self.close_connection:
                self.add_message("Ошибка: Не удалось получить функции WebSocket")
                return
                
            # Тестовое сообщение для проверки соединения
            try:
                self.send_message("CONNECT_TEST")
                self.add_message("Тестовое сообщение отправлено")
            except Exception as e:
                self.add_message(f"Ошибка при отправке тестового сообщения: {str(e)}")
            
            # Запускаем поток для прослушивания сообщений
            self.is_connected = True
            self.listener_thread = threading.Thread(target=self.listen_for_messages)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            self.connection_status_changed.emit(True, f"Подключено к {host}:{port}")
            
        except Exception as e:
            self.add_message(f"Ошибка подключения: {str(e)}")

    def disconnect_from_server(self):
        if self.close_connection:
            try:
                self.close_connection()
                self.add_message("Соединение закрыто")
            except Exception as e:
                self.add_message(f"Ошибка при закрытии соединения: {str(e)}")
                
        self.is_connected = False
        self.connection_status_changed.emit(False, "Отключено")
        
        # Сбрасываем функции
        self.send_message = None
        self.receive_message = None
        self.close_connection = None

    def listen_for_messages(self):
        # Используем сигнал для безопасного обновления UI из другого потока
        log("Запущен поток прослушивания сообщений")
        
        # Отправляем сообщение через сигнал (безопасно)
        self.message_received.emit("Запущен поток прослушивания сообщений")
        
        message_count = 0
        while self.is_connected and self.receive_message:
            try:
                message = self.receive_message()
                if message:
                    # Добавляем отладочное сообщение
                    log(f"Получено сырое сообщение от сервера: {message}")
                    
                    # Используем сигнал для безопасного обновления UI из другого потока
                    message_text = f"Получено: {message}"
                    log(message_text)  # Отладка в консоль
                    
                    # Отправляем сообщение через сигнал
                    self.message_received.emit(message_text)
                    
                    # Проверяем, является ли сообщение Python-кодом для выполнения
                    # Добавляем отладочное сообщение
                    log("Вызываем process_received_message для обработки сообщения")
                    self.process_received_message(message)
                    
                    # Увеличиваем счетчик сообщений
                    message_count += 1
                    log(f"Всего получено сообщений: {message_count}")
                    
                # Небольшая задержка, чтобы не нагружать CPU
                time.sleep(0.1)
            except Exception as e:
                error_msg = f"Ошибка при получении сообщения: {str(e)}"
                log(error_msg)  # Отладочная информация в консоль
                
                # Отправляем сообщение об ошибке через сигнал
                self.message_received.emit(error_msg)
                
                self.is_connected = False
                self.connection_status_changed.emit(False, "Отключено из-за ошибки")
                break
        
        # Отправляем сообщение о завершении через сигнал
        self.message_received.emit("Поток прослушивания сообщений завершен")
        log("Поток прослушивания сообщений завершен")

    def send_message_to_server(self):
        if not self.is_connected or not self.send_message:
            self.add_message("Ошибка: Нет активного соединения")
            return
            
        message = self.message_input.text()
        if not message:
            return
            
        try:
            self.send_message(message)
            self.add_message(f"Отправлено: {message}")
            self.message_input.clear()
        except Exception as e:
            self.add_message(f"Ошибка при отправке сообщения: {str(e)}")

    def add_message(self, message):
        """Добавляет сообщение в область отображения"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.messages_display.append(formatted_message)
        # Прокручиваем до последнего сообщения
        self.messages_display.verticalScrollBar().setValue(
            self.messages_display.verticalScrollBar().maximum()
        )
        # Отладка в консоль
        log(f"Добавлено сообщение в UI: {formatted_message}")

    def update_messages(self, message):
        """Обновляет область сообщений (вызывается из другого потока через сигнал)"""
        log(f"update_messages вызван с сообщением: {message}")
        self.add_message(message)

    def update_connection_status(self, is_connected, status_text):
        """Обновляет статус соединения (вызывается из другого потока через сигнал)"""
        self.status_label.setText(f"Статус: {status_text}")
        
        # Обновляем состояние кнопки подключения
        if is_connected:
            self.connect_button.setText("Отключиться")
            self.message_input.setEnabled(True)
            self.send_button.setEnabled(True)
        else:
            self.connect_button.setText("Подключиться")
            self.message_input.setEnabled(False)
            self.send_button.setEnabled(False)

    def clear_messages(self):
        """Очищает область сообщений"""
        self.messages_display.clear()

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.is_connected:
            self.disconnect_from_server()
        event.accept()
        
    # Функции для выполнения Python-кода
    
    def process_received_message(self, message):
        """
        Обрабатывает полученное сообщение и выполняет Python-код из поля python_code в JSON.
        Если сообщение не в формате JSON, выводит его как информационное сообщение.
        
        Args:
            message (str): Полученное сообщение от сервера
        """
        try:
            # Добавляем отладочное сообщение
            log(f"Обработка сообщения: {message}")
            
            # Проверяем, не является ли сообщение уже строкой JSON
            # Иногда WebSocket может добавлять кавычки вокруг JSON
            if message.startswith('"') and message.endswith('"'):
                try:
                    # Пытаемся удалить внешние кавычки и распарсить
                    unquoted_message = json.loads(message)
                    if isinstance(unquoted_message, str):
                        log(f"Сообщение было в кавычках, пробуем распарсить внутреннее содержимое: {unquoted_message}")
                        message = unquoted_message
                except Exception as e:
                    log(f"Ошибка при попытке удалить кавычки: {str(e)}")
            
            # Пытаемся распарсить сообщение как JSON
            try:
                data = json.loads(message)
                # Добавляем отладочное сообщение
                log(f"Сообщение успешно распарсено как JSON: {data}")
                
                # Проверяем, содержит ли JSON поле с Python-кодом
                if isinstance(data, dict) and 'python_code' in data:
                    code = data['python_code']
                    # Добавляем отладочное сообщение
                    log(f"Найден python_code: {code}")
                    # Используем сигнал для выполнения кода в главном потоке
                    self.execute_code_signal.emit(code)
                # Проверяем наличие вызова функции
                elif isinstance(data, dict) and 'function_call' in data:
                    function_name = data['function_call']
                    # Извлекаем аргументы (если они есть)
                    function_args = data.get('arguments', {})
                    # Добавляем отладочное сообщение
                    log(f"Найден function_call: {function_name}, аргументы: {function_args}")
                    # Используем сигнал для выполнения функции в главном потоке
                    self.execute_function_signal.emit(function_name, function_args)
                else:
                    log(f"В сообщении JSON отсутствует поле 'python_code' или 'function_call'")
                    # Выводим информационное сообщение о полученных данных
                    self.message_received.emit(f"Информация: Получены данные: {json.dumps(data, ensure_ascii=False)}")
                    
            except json.JSONDecodeError as e:
                # Добавляем отладочное сообщение
                log(f"Сообщение не является JSON: {str(e)}")
                
                # Просто выводим сообщение как информационное
                self.message_received.emit(f"Информация: {message}")
                
        except Exception as e:
            error_msg = f"Ошибка при обработке сообщения: {str(e)}"
            log(error_msg)
            self.message_received.emit(error_msg)
    
    def execute_code_in_main_thread(self, code):
        """
        Выполняет Python-код в главном потоке и отправляет результат на сервер через WebSocket
        
        Args:
            code (str): Python-код для выполнения
        """
        try:
            # Добавляем отладочное сообщение
            log(f"Выполнение кода в главном потоке: {code}")
            
            self.add_message(f"Выполнение Python-кода...")
            
            # Создаем функцию отправки результатов через веб-сокет
            def websocket_sender(data):
                if self.is_connected and self.send_message:
                    try:
                        # Преобразуем данные в JSON
                        json_data = json.dumps(data)
                        # Отправляем через веб-сокет
                        self.send_message(json_data)
                        self.add_message(f"Результат отправлен на сервер")
                    except Exception as e:
                        self.add_message(f"Ошибка при отправке результата: {str(e)}")
                else:
                    self.add_message("Не удалось отправить результат: нет подключения к серверу")
            
            # Настраиваем executor для отправки результатов через веб-сокет
            self.freecad_executor.websocket_sender = websocket_sender
            
            # Используем FreeCADExecutor для выполнения кода с отправкой результата
            result = self.freecad_executor.execute_code(code, send_result=True)
            
            # Добавляем отладочное сообщение
            log(f"Результат выполнения: {result}")
            
            if result['success']:
                self.add_message(result['message'])
                
                # Если есть результат, выводим его
                if 'result' in result and result['result']:
                    self.add_message(f"Результат: {json.dumps(result['result'], ensure_ascii=False)}")
            else:
                error_msg = f"Ошибка при выполнении Python-кода: {result.get('error', 'Неизвестная ошибка')}"
                self.add_message(error_msg)
                
                # Если есть трассировка, выводим её
                if 'traceback' in result:
                    self.add_message(f"Трассировка: {result['traceback']}")
                
        except Exception as e:
            error_msg = f"Ошибка при выполнении Python-кода: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            self.add_message(error_msg)

    def execute_function_in_main_thread(self, function_name, function_args):
        """
        Выполняет вызов функции в главном потоке и отправляет результат на сервер
        
        Args:
            function_name (str): Имя функции для вызова
            function_args (dict): Аргументы функции
        """
        try:
            # Добавляем отладочное сообщение
            log(f"Выполнение функции в главном потоке: {function_name} с аргументами: {function_args}")
            
            self.add_message(f"Выполнение функции: {function_name}...")
            
            # Создаем функцию отправки результатов через веб-сокет (аналогично execute_code_in_main_thread)
            def websocket_sender(data):
                if self.is_connected and self.send_message:
                    try:
                        # Преобразуем данные в JSON
                        json_data = json.dumps(data)
                        # Отправляем через веб-сокет
                        self.send_message(json_data)
                        self.add_message(f"Результат отправлен на сервер")
                    except Exception as e:
                        self.add_message(f"Ошибка при отправке результата: {str(e)}")
                else:
                    self.add_message("Не удалось отправить результат: нет подключения к серверу")
            
            # Передаем функцию отправки в реестр функций
            self.function_registry.websocket_sender = websocket_sender
            
            # Вызываем функцию из реестра и получаем результат
            result = self.function_registry.execute_function(function_name, function_args)
            
            # Добавляем отладочное сообщение
            log(f"Результат выполнения функции: {result}")
            
            # Отправляем результат на сервер
            if self.is_connected and self.send_message:
                try:
                    response_data = {
                        "function_response": function_name,
                        "result": result
                    }
                    json_response = json.dumps(response_data)
                    self.send_message(json_response)
                    self.add_message(f"Результат функции {function_name} отправлен на сервер")
                except Exception as e:
                    error_msg = f"Ошибка при отправке результата функции: {str(e)}"
                    log(error_msg)
                    self.add_message(error_msg)
            
            # Выводим информацию о выполнении в UI
            self.add_message(f"Функция {function_name} выполнена успешно")
            if result:
                self.add_message(f"Результат: {json.dumps(result, ensure_ascii=False)}")
                
        except Exception as e:
            error_msg = f"Ошибка при выполнении функции {function_name}: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            self.add_message(error_msg)
            
            # Отправляем информацию об ошибке на сервер
            if self.is_connected and self.send_message:
                try:
                    error_data = {
                        "function_response": function_name,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                    json_error = json.dumps(error_data)
                    self.send_message(json_error)
                except Exception as send_error:
                    self.add_message(f"Ошибка при отправке информации об ошибке: {str(send_error)}")

    def set_plm_functions(self, plm_functions: PLMFunctions):
        """
        Устанавливает PLMFunctions и регистрирует их в реестре функций
        
        Args:
            plm_functions: Экземпляр PLMFunctions
        """
        self.plm_functions = plm_functions
        
        if self.plm_functions:
            # Регистрируем функции PLM в реестре
            self.plm_functions.register_functions(self.function_registry)
            self.add_message("Функции PLM зарегистрированы в реестре")
            log("PLM функции успешно зарегистрированы в реестре функций клиентской панели") 