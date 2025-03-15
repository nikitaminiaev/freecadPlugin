import json
import threading
import time
from PySide2 import QtWidgets, QtCore, QtGui

from socket_client import create_websocket_client


class PLMClientWindow(QtWidgets.QWidget):
    # Сигнал для обновления UI из другого потока
    message_received = QtCore.Signal(str)
    connection_status_changed = QtCore.Signal(bool, str)

    def __init__(self):
        super().__init__()
        self.send_message = None
        self.receive_message = None
        self.close_connection = None
        self.listener_thread = None
        self.is_connected = False
        self.setup_ui()
        
        # Подключаем сигналы
        self.message_received.connect(self.update_messages)
        self.connection_status_changed.connect(self.update_connection_status)

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
            
            # Запускаем поток для прослушивания сообщений
            self.listener_thread = threading.Thread(target=self.listen_for_messages)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            self.is_connected = True
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
        while self.is_connected and self.receive_message:
            try:
                message = self.receive_message()
                if message:
                    self.message_received.emit(f"Получено: {message}")
                    self.add_message(f"Получено: {message}")
                time.sleep(0.1)  # Небольшая задержка
            except Exception as e:
                self.message_received.emit(f"Ошибка при получении сообщения: {str(e)}")
                self.is_connected = False
                self.connection_status_changed.emit(False, "Отключено из-за ошибки")
                break

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

    def update_messages(self, message):
        """Обновляет область сообщений (вызывается из другого потока через сигнал)"""
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