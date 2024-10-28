import json

from PySide2 import QtWidgets

from cad_utils import CADUtils
from models import BasicObject
from widgets import ObjectTreeWidget
from api_client import APIClient


class PLMMainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle('PLM')
        self.setGeometry(100, 100, 600, 400)

        layout = QtWidgets.QVBoxLayout(self)

        # Search area
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

        # Tree widget
        self.resultsTree = ObjectTreeWidget()
        layout.addWidget(self.resultsTree)

    def search_part(self):
        part_name = self.textInput.text()
        if not part_name:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please enter a part name!')
            return

        try:
            response = self.api_client.send_get_request("/api/basic_object", query_params={"name": part_name})
            data = json.loads(response)

            if isinstance(data, dict) and 'error' in data:
                QtWidgets.QMessageBox.critical(self, 'Error', str(data['error']))
                return

            objects = BasicObject.from_response(data)
            if objects:
                self.resultsTree.display_hierarchical_results(
                    objects if isinstance(objects, list) else [objects],
                    is_search_result=True,
                    load_callback=self.load_object
                )
            else:
                QtWidgets.QMessageBox.information(self, 'Information', 'No objects found with this name!')
                self.resultsTree.clear()

        except Exception as e:
            print(f"Exception in search_part: {str(e)}")
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
            self.resultsTree.clear()

    def find_all_parts(self):
        try:
            response = self.api_client.send_get_request("/api/basic_objects")
            data = json.loads(response)

            if isinstance(data, dict) and 'error' in data:
                QtWidgets.QMessageBox.critical(self, 'Error', str(data['error']))
                return

            objects = BasicObject.from_response(data)
            if objects:
                self.resultsTree.display_hierarchical_results(
                    objects,
                    is_search_result=False,
                    load_callback=self.load_object
                )
            else:
                QtWidgets.QMessageBox.information(self, 'Information', 'No objects found!')
                self.resultsTree.clear()

        except Exception as e:
            print(f"Exception in find_all_parts: {str(e)}")
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
            self.resultsTree.clear()

    def load_object(self, part_id):
        try:
            response = self.api_client.send_get_request(
                "/api/basic_object/{id}",
                path_params={"id": part_id}
            )
            data = json.loads(response)
            obj = BasicObject(data)

            if obj.file_path:
                QtWidgets.QMessageBox.information(self, 'Success', f'Part found: {obj.file_path}')
                try:
                    CADUtils.open_file(obj.file_path)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, 'Error', str(e))
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'Object found, but no file path available!')

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while loading the object: {str(e)}')