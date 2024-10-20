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
        self.setWindowTitle('Search Obj by Name')
        self.setGeometry(100, 100, 500, 150)  # Adjusted width and reduced height

        layout = QtWidgets.QVBoxLayout(self)

        # Search input area
        search_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel('Enter Obj Name:')
        self.textInput = QtWidgets.QLineEdit()
        self.submitButton = QtWidgets.QPushButton('Search')
        self.submitButton.clicked.connect(self.search_part)

        search_layout.addWidget(self.label)
        search_layout.addWidget(self.textInput)
        search_layout.addWidget(self.submitButton)

        layout.addLayout(search_layout)

        # Results area (initially hidden)
        self.results_widget = QtWidgets.QWidget()
        results_layout = QtWidgets.QHBoxLayout(self.results_widget)

        self.nameLabel = QtWidgets.QLabel('Obj Name:')
        self.nameOutput = QtWidgets.QLabel()
        self.idLabel = QtWidgets.QLabel('Obj ID:')
        self.idOutput = QtWidgets.QLabel()
        self.actionButton = QtWidgets.QPushButton('Load')
        self.actionButton.clicked.connect(self.load_object)

        results_layout.addWidget(self.nameLabel)
        results_layout.addWidget(self.nameOutput)
        results_layout.addWidget(self.idLabel)
        results_layout.addWidget(self.idOutput)
        results_layout.addWidget(self.actionButton)

        layout.addWidget(self.results_widget)

        # Initially hide the results
        self.results_widget.hide()

        # Храним ID детали для дальнейшего использования
        self.part_id = None

    def search_part(self):
        part_name = self.textInput.text()
        if not part_name:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please enter a part name!')
            return

        try:
            query_params = {"name": part_name}
            response = send_get_request("/api/basic_object", query_params=query_params)
            data = json.loads(response)

            if data and 'basic_object' in data:
                part_name = data['basic_object'].get('name', 'N/A')
                part_id = data['basic_object'].get('id', 'N/A')

                self.nameOutput.setText(part_name)
                self.idOutput.setText(str(part_id))
                self.part_id = part_id

                # Show the results
                self.results_widget.show()
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'No objects found with this name!')
                self.results_widget.hide()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
            self.results_widget.hide()

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
