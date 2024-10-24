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
        self.setGeometry(100, 100, 600, 400)

        layout = QtWidgets.QVBoxLayout(self)

        # Search input area
        search_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel('Enter Obj Name:')
        self.textInput = QtWidgets.QLineEdit()
        self.submitButton = QtWidgets.QPushButton('Search')
        self.findAllButton = QtWidgets.QPushButton('Find All')
        self.submitButton.clicked.connect(self.search_part)
        self.findAllButton.clicked.connect(self.find_all_parts)

        search_layout.addWidget(self.label)
        search_layout.addWidget(self.textInput)
        search_layout.addWidget(self.submitButton)
        search_layout.addWidget(self.findAllButton)

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

        # Add table for multiple results
        self.resultsTable = QtWidgets.QTableWidget()
        self.resultsTable.setColumnCount(3)
        self.resultsTable.setHorizontalHeaderLabels(['Name', 'ID', 'Actions'])
        self.resultsTable.horizontalHeader().setStretchLastSection(True)
        self.resultsTable.verticalHeader().setVisible(False)
        self.resultsTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(self.resultsTable)
        self.resultsTable.hide()

        # Initially hide the results
        self.results_widget.hide()

        # Store part ID
        self.part_id = None

    class LoadButton(QtWidgets.QPushButton):
        def __init__(self, part_id, parent=None):
            super().__init__('Load', parent)
            self.part_id = part_id

    def display_multiple_results(self, objects):
        self.results_widget.hide()
        self.resultsTable.show()
        self.resultsTable.setRowCount(len(objects))

        for row, obj in enumerate(objects):
            # Name column
            name_item = QtWidgets.QTableWidgetItem(obj.get('name', 'N/A'))
            self.resultsTable.setItem(row, 0, name_item)

            # ID column
            part_id = str(obj.get('id', 'N/A'))
            id_item = QtWidgets.QTableWidgetItem(part_id)
            self.resultsTable.setItem(row, 1, id_item)

            # Action button column
            load_button = self.LoadButton(part_id)
            load_button.clicked.connect(self.handle_load_button)
            self.resultsTable.setCellWidget(row, 2, load_button)

        self.resultsTable.resizeColumnsToContents()

    def handle_load_button(self):
        button = self.sender()
        if isinstance(button, self.LoadButton):
            self.part_id = button.part_id
            self.load_object()

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

                # Show single result
                self.results_widget.show()
                self.resultsTable.hide()
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'No objects found with this name!')
                self.results_widget.hide()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
            self.results_widget.hide()

    def find_all_parts(self):
        try:
            response = send_get_request("/api/basic_objects")
            data = json.loads(response)

            if data and 'basic_objects' in data:
                objects = data['basic_objects']
                self.display_multiple_results(objects)
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'No objects found!')
                self.resultsTable.hide()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
            self.resultsTable.hide()

    def load_object(self):
        if self.part_id:
            try:
                path_params = {"id": self.part_id}
                response = send_get_request("/api/basic_object/{id}", path_params=path_params)
                data = json.loads(response)
                print(data)

                file_path = data.get('bounding_contour', {}).get('brep_files', {}).get('path')

                if file_path:
                    QtWidgets.QMessageBox.information(self, 'Success', f'Part found: {file_path}')
                    import FreeCAD
                    FreeCAD.open(file_path)
                else:
                    QtWidgets.QMessageBox.critical(self, 'Error', 'Object found, but no file path available!')
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {e}')
        else:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'No part selected!')