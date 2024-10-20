import json
from PySide2 import QtWidgets, QtCore
import http.client


class MyDialog(QtWidgets.QDialog):
    def __init__(self):
        super(MyDialog, self).__init__()
        self.setWindowTitle('My Custom Form')
        self.setGeometry(100, 100, 400, 200)

        # Создаем элементы интерфейса
        self.label = QtWidgets.QLabel('Enter Data:', self)
        self.label.setGeometry(QtCore.QRect(20, 20, 100, 30))

        self.textInput = QtWidgets.QLineEdit(self)
        self.textInput.setGeometry(QtCore.QRect(120, 20, 200, 30))

        self.submitButton = QtWidgets.QPushButton('Submit', self)
        self.submitButton.setGeometry(QtCore.QRect(150, 100, 100, 30))

        # Подключаем событие нажатия кнопки к методу
        self.submitButton.clicked.connect(self.send_http_request)

    def send_http_request(self):
        # Получаем данные из формы
        user_input = self.textInput.text()

        # Пример отправки HTTP-запроса с использованием http.client
        conn = http.client.HTTPConnection("example.com")  # Замените на нужный вам домен
        headers = {'Content-type': 'application/json'}
        payload = json.dumps({'data': user_input})

        try:
            conn.request("POST", "/api", payload, headers)  # Замените "/api" на нужный вам путь
            response = conn.getresponse()

            # Проверяем статус ответа
            if response.status == 200:
                QtWidgets.QMessageBox.information(self, 'Success', 'Request was successful!')
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', f'Failed to send request! Status: {response.status}')

            conn.close()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
