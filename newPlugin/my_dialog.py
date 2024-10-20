import json
from PySide2 import QtWidgets, QtCore
import http.client


def send_get_request(url_template: str, path_params: dict = None, query_params: dict = None):
    conn = http.client.HTTPConnection("localhost", port=8000)

    if path_params is not None and len(query_params) > 0:
        for key, value in path_params.items():
            full_url = url_template.replace(f"{{{key}}}", str(value))
            print(full_url)
    elif query_params and len(query_params) > 0:
        full_url = url_template + "?" + "&".join([f"{key}={value}" for key, value in query_params.items()])
    else:
        full_url = url_template

    print(full_url)

    conn.request("GET", full_url)
    response = conn.getresponse()

    print(response.status, response.reason)

    data = response.read()
    conn.close()

    return data.decode("utf-8")

class MyDialog(QtWidgets.QDialog):
    def __init__(self):
        super(MyDialog, self).__init__()
        self.setWindowTitle('Search Part by Name')
        self.setGeometry(100, 100, 400, 200)

        # Создаем элементы интерфейса
        self.label = QtWidgets.QLabel('Enter Part Name:', self)
        self.label.setGeometry(QtCore.QRect(20, 20, 100, 30))

        self.textInput = QtWidgets.QLineEdit(self)
        self.textInput.setGeometry(QtCore.QRect(120, 20, 200, 30))

        self.submitButton = QtWidgets.QPushButton('Search', self)
        self.submitButton.setGeometry(QtCore.QRect(150, 100, 100, 30))

        # Подключаем событие нажатия кнопки к методу
        self.submitButton.clicked.connect(self.search_part)

    def search_part(self):
        # Получаем данные из формы
        part_name = self.textInput.text()

        # Проверка, что поле ввода не пустое
        if not part_name:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please enter a part name!')
            return

        # Пример отправки GET-запроса для поиска детали по имени
        try:
            query_params = {"name": part_name}
            response = send_get_request("/api/basic_object", query_params=query_params)

            # Парсим ответ
            data = json.loads(response)
            print(data)
            # Проверяем, найдено ли что-то
            if data:
                file_path = data['basic_object']['bounding_contour']['brep_files']['path']
                print(file_path)
                if file_path:
                    QtWidgets.QMessageBox.information(self, 'Success', f'Part found: {file_path}')
                    # Можно открыть файл в FreeCAD, как показано в вашем примере
                    import FreeCAD
                    FreeCAD.open(file_path)
                else:
                    QtWidgets.QMessageBox.critical(self, 'Error', 'Object found, but no file path available!')
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'No objects found with this name!')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
