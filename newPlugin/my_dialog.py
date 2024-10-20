import json
from PySide2 import QtWidgets, QtCore
import http.client


def send_get_request(url_template: str, path_params: dict = None, query_params: dict = None):
    conn = http.client.HTTPConnection("localhost", port=8000)

    try:
        if path_params:
            full_url = url_template
            for key, value in path_params.items():
                full_url = full_url.replace(f"{{{key}}}", str(value))
        elif query_params:
            full_url = url_template + "?" + "&".join([f"{key}={value}" for key, value in query_params.items()])
        else:
            full_url = url_template

        print(f"Requesting URL: {full_url}")

        conn.request("GET", full_url)
        response = conn.getresponse()

        print(f"Response status: {response.status} {response.reason}")

        if response.status == 200:
            data = response.read()
            return data.decode("utf-8")
        else:
            print(f"Error response: {response.status} {response.reason}")
            return json.dumps({"error": f"HTTP {response.status}: {response.reason}"})

    except Exception as e:
        print(f"Exception in send_get_request: {str(e)}")
        return json.dumps({"error": str(e)})

    finally:
        conn.close()

class MyDialog(QtWidgets.QDialog):
    def __init__(self):
        super(MyDialog, self).__init__()
        self.setWindowTitle('Search Part by Name')
        self.setGeometry(100, 100, 400, 300)

        # Поле для ввода имени
        self.label = QtWidgets.QLabel('Enter Part Name:', self)
        self.label.setGeometry(QtCore.QRect(20, 20, 100, 30))

        self.textInput = QtWidgets.QLineEdit(self)
        self.textInput.setGeometry(QtCore.QRect(120, 20, 200, 30))

        # Кнопка для поиска
        self.submitButton = QtWidgets.QPushButton('Search', self)
        self.submitButton.setGeometry(QtCore.QRect(150, 70, 100, 30))
        self.submitButton.clicked.connect(self.search_part)

        # Поля для отображения найденной информации о детали
        self.nameLabel = QtWidgets.QLabel('Part Name:', self)
        self.nameLabel.setGeometry(QtCore.QRect(20, 120, 100, 30))
        self.nameOutput = QtWidgets.QLabel(self)
        self.nameOutput.setGeometry(QtCore.QRect(120, 120, 200, 30))

        self.idLabel = QtWidgets.QLabel('Part ID:', self)
        self.idLabel.setGeometry(QtCore.QRect(20, 160, 100, 30))
        self.idOutput = QtWidgets.QLabel(self)
        self.idOutput.setGeometry(QtCore.QRect(120, 160, 200, 30))

        # Кнопка для действия с найденной деталью (например, передача id)
        self.actionButton = QtWidgets.QPushButton('Load', self)
        self.actionButton.setGeometry(QtCore.QRect(150, 220, 100, 30))
        self.actionButton.clicked.connect(self.load_object)
        self.actionButton.setEnabled(False)  # Отключаем кнопку, пока не найдена деталь

        # Храним ID детали для дальнейшего использования
        self.part_id = None

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
                # file_path = data['basic_object']['bounding_contour']['brep_files']['path']
                # Извлекаем имя и id
                part_name = data['basic_object']['name'] # get('name')
                part_id = data['basic_object']['id']

                # Отображаем данные на интерфейсе
                self.nameOutput.setText(part_name)
                self.idOutput.setText(part_id)

                # Сохраняем id для дальнейшего использования
                self.part_id = part_id

                # Включаем кнопку для действия
                self.actionButton.setEnabled(True)

                # print(file_path)
                # if file_path:
                #     QtWidgets.QMessageBox.information(self, 'Success', f'Part found: {file_path}')
                #     # Можно открыть файл в FreeCAD, как показано в вашем примере
                #     import FreeCAD
                #     FreeCAD.open(file_path)
                # else:
                #     QtWidgets.QMessageBox.critical(self, 'Error', 'Object found, but no file path available!')
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'No objects found with this name!')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {e}')

    def load_object(self):
        # Проверяем, есть ли id детали
        if self.part_id:
            try:
                # Создаем словарь с id для path_params
                path_params = {"id": self.part_id}
                response = send_get_request("/api/basic_object/{id}", path_params=path_params)

                # Парсим ответ
                data = json.loads(response)
                print(data)

                # Предполагаем, что путь к файлу находится в этом месте структуры JSON
                file_path = data.get('bounding_contour', {}).get('brep_files', {}).get('path')

                if file_path:
                    QtWidgets.QMessageBox.information(self, 'Success', f'Part found: {file_path}')
                    # Можно открыть файл в FreeCAD, как показано в вашем примере
                    import FreeCAD
                    FreeCAD.open(file_path)
                else:
                    QtWidgets.QMessageBox.critical(self, 'Error', 'Object found, but no file path available!')
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
        else:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'No part selected!')
