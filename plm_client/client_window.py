import json
import threading
import time
from PySide2 import QtWidgets, QtCore

from socket_client import create_websocket_client

# Добавляем импорт для выполнения кода
import traceback
from freecad_executor import FreeCADExecutor

class PLMClientWindow(QtWidgets.QWidget):
    # Сигнал для обновления UI из другого потока
    message_received = QtCore.Signal(str)
    connection_status_changed = QtCore.Signal(bool, str)
    # Добавляем сигнал для выполнения кода в главном потоке
    execute_code_signal = QtCore.Signal(str)
    # Добавляем сигнал для показа диалога в главном потоке
    show_dialog_signal = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self.send_message = None
        self.receive_message = None
        self.close_connection = None
        self.listener_thread = None
        self.is_connected = False
        
        # Создаем экземпляр FreeCADExecutor
        self.freecad_executor = FreeCADExecutor(logger_callback=self.add_message)
        
        self.setup_ui()
        
        # Подключаем сигналы
        self.message_received.connect(self.update_messages)
        self.connection_status_changed.connect(self.update_connection_status)
        # Подключаем сигнал для выполнения кода
        self.execute_code_signal.connect(self.execute_code_in_main_thread)
        # Подключаем сигнал для показа диалога
        self.show_dialog_signal.connect(self._show_execute_dialog)

    def setup_ui(self):
        self.setWindowTitle('PLM Client')
        self.setGeometry(100, 100, 600, 400)

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
        # ВАЖНО: Нельзя напрямую вызывать self.add_message из другого потока!
        # Это может привести к краху приложения, так как UI должен обновляться только из главного потока
        print("Запущен поток прослушивания сообщений")
        
        # Отправляем сообщение через сигнал (безопасно)
        self.message_received.emit("Запущен поток прослушивания сообщений")
        
        message_count = 0
        while self.is_connected and self.receive_message:
            try:
                message = self.receive_message()
                if message:
                    # Добавляем отладочное сообщение
                    print(f"Получено сырое сообщение от сервера: {message}")
                    
                    # Используем сигнал для безопасного обновления UI из другого потока
                    message_text = f"Получено: {message}"
                    print(message_text)  # Отладка в консоль
                    
                    # Отправляем сообщение через сигнал
                    self.message_received.emit(message_text)
                    
                    # Проверяем, является ли сообщение Python-кодом для выполнения
                    # Добавляем отладочное сообщение
                    print("Вызываем process_received_message для обработки сообщения")
                    self.process_received_message(message)
                    
                    # Увеличиваем счетчик сообщений
                    message_count += 1
                    print(f"Всего получено сообщений: {message_count}")
                    
                # Небольшая задержка, чтобы не нагружать CPU
                time.sleep(0.1)
            except Exception as e:
                error_msg = f"Ошибка при получении сообщения: {str(e)}"
                print(error_msg)  # Отладочная информация в консоль
                
                # Отправляем сообщение об ошибке через сигнал
                self.message_received.emit(error_msg)
                
                self.is_connected = False
                self.connection_status_changed.emit(False, "Отключено из-за ошибки")
                break
        
        # Отправляем сообщение о завершении через сигнал
        self.message_received.emit("Поток прослушивания сообщений завершен")
        print("Поток прослушивания сообщений завершен")

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
        print(f"Добавлено сообщение в UI: {formatted_message}")

    def update_messages(self, message):
        """Обновляет область сообщений (вызывается из другого потока через сигнал)"""
        print(f"update_messages вызван с сообщением: {message}")
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
        Обрабатывает полученное сообщение и определяет, является ли оно Python-кодом для выполнения
        
        Args:
            message (str): Полученное сообщение от сервера
        """
        try:
            # Добавляем отладочное сообщение
            print(f"Обработка сообщения: {message}")
            
            # Проверяем, не начинается ли сообщение с "Получено: "
            if message.startswith("Получено: "):
                # Удаляем префикс "Получено: "
                message = message[len("Получено: "):]
                print(f"Удален префикс 'Получено: ', новое сообщение: {message}")
            
            # Проверяем, не начинается ли сообщение с "Сервер получил: "
            if message.startswith("Сервер получил: "):
                # Это эхо-ответ от сервера, не обрабатываем его как код
                print(f"Обнаружено эхо-сообщение от сервера, пропускаем обработку")
                return
            
            # Проверяем, не является ли сообщение уже строкой JSON
            # Иногда WebSocket может добавлять кавычки вокруг JSON
            if message.startswith('"') and message.endswith('"'):
                try:
                    # Пытаемся удалить внешние кавычки и распарсить
                    unquoted_message = json.loads(message)
                    if isinstance(unquoted_message, str):
                        print(f"Сообщение было в кавычках, пробуем распарсить внутреннее содержимое: {unquoted_message}")
                        message = unquoted_message
                except Exception as e:
                    print(f"Ошибка при попытке удалить кавычки: {str(e)}")
            
            # Пытаемся распарсить сообщение как JSON
            try:
                data = json.loads(message)
                # Добавляем отладочное сообщение
                print(f"Сообщение успешно распарсено как JSON: {data}")
                
                # Проверяем, содержит ли JSON поле с Python-кодом
                if isinstance(data, dict):
                    # Добавляем отладочное сообщение
                    print(f"Ключи в JSON: {list(data.keys())}")
                    
                    # Если есть поле python_code, выполняем код
                    if 'python_code' in data:
                        code = data['python_code']
                        # Добавляем отладочное сообщение
                        print(f"Найден python_code: {code}")
                        # Используем сигнал для выполнения кода в главном потоке
                        self.execute_code_signal.emit(code)
                        return
                        
            except json.JSONDecodeError as e:
                # Добавляем отладочное сообщение
                print(f"Ошибка при разборе JSON: {str(e)}")
                # Если сообщение не является JSON, проверяем другие форматы
                pass
                
            # Проверяем, начинается ли сообщение с маркера Python-кода
            if message.startswith('EXEC_PYTHON:'):
                code = message[len('EXEC_PYTHON:'):].strip()
                # Используем сигнал для выполнения кода в главном потоке
                self.execute_code_signal.emit(code)
                return
                
            # Проверяем, является ли сообщение простым Python-кодом
            # Список распространенных функций и операторов Python
            python_functions = ['print(', 'len(', 'range(', 'str(', 'int(', 'float(', 'list(', 'dict(', 'set(', 'tuple(']
            python_keywords = ['import', 'def ', 'class ', 'for ', 'while ', 'if ', 'else:', 'elif ', 'try:', 'except:', 'with ', 'return ', 'yield ', 'lambda ']
            freecad_keywords = ['FreeCAD', 'App.', 'Gui.', 'Part.', 'Draft.', 'Mesh.', 'Sketcher.', 'PartDesign.']
            
            # Если сообщение содержит любую из этих строк, считаем его Python-кодом
            is_python_code = False
            
            # Проверяем на наличие функций Python
            if any(func in message for func in python_functions):
                is_python_code = True
            
            # Проверяем на наличие ключевых слов Python
            if any(keyword in message for keyword in python_keywords):
                is_python_code = True
                
            # Проверяем на наличие ключевых слов FreeCAD
            if any(keyword in message for keyword in freecad_keywords):
                is_python_code = True
                
            # Проверяем, содержит ли сообщение операторы присваивания или математические операции
            if '=' in message and not '==' in message:
                is_python_code = True
                
            # Если сообщение выглядит как Python-код, выполняем его
            if is_python_code:
                # Для простых команд выполняем без подтверждения
                if len(message) < 50 and ('print(' in message or 'FreeCAD' in message):
                    self.execute_code_signal.emit(message)
                else:
                    # Для более сложных команд спрашиваем подтверждение
                    self.ask_to_execute_code(message)
                return
                
        except Exception as e:
            error_msg = f"Ошибка при обработке сообщения: {str(e)}"
            print(error_msg)
            self.message_received.emit(error_msg)
    
    def ask_to_execute_code(self, code):
        """
        Спрашивает пользователя, выполнять ли полученный код
        
        Args:
            code (str): Python-код для выполнения
        """
        # Сохраняем код для использования в диалоге
        self._pending_code = code
        
        # Используем сигнал для безопасного создания диалога в главном потоке
        self.show_dialog_signal.emit(code)
    
    def _show_execute_dialog(self, code):
        """
        Показывает диалог для подтверждения выполнения кода в главном потоке
        
        Args:
            code (str): Python-код для выполнения
        """
        try:
            reply = QtWidgets.QMessageBox.question(
                self, 
                'Выполнить код?',
                f'Получен Python-код. Выполнить его?\n\n{code[:200]}{"..." if len(code) > 200 else ""}',
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.execute_code_in_main_thread(code)
        except Exception as e:
            error_msg = f"Ошибка при создании диалога: {str(e)}"
            print(error_msg)
            self.message_received.emit(error_msg)
    
    def execute_code_in_main_thread(self, code):
        """
        Выполняет Python-код в главном потоке и отправляет результат на сервер через WebSocket
        
        Args:
            code (str): Python-код для выполнения
        """
        try:
            # Добавляем отладочное сообщение
            print(f"Выполнение кода в главном потоке: {code}")
            
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
            
            # Проверяем, является ли код простой командой
            if code.strip().startswith('print(') or len(code.strip().split('\n')) == 1:
                # Добавляем отладочное сообщение
                print(f"Выполнение простой команды: {code}")
                # Используем метод для выполнения простых команд с отправкой результата
                result = self.freecad_executor.execute_simple_command(code, send_result=True)
            else:
                # Добавляем отладочное сообщение
                print(f"Выполнение сложного кода")
                # Используем FreeCADExecutor для выполнения кода с отправкой результата
                result = self.freecad_executor.execute_code(code, send_result=True)
            
            # Добавляем отладочное сообщение
            print(f"Результат выполнения: {result}")
            
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
            print(error_msg)
            self.add_message(error_msg)