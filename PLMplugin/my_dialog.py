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
        self.setWindowTitle('PLM')
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

        # Tree widget setup
        self.resultsTree = QtWidgets.QTreeWidget()
        self.resultsTree.setColumnCount(3)
        self.resultsTree.setHeaderLabels(['Name', 'ID', 'Actions'])

        header = self.resultsTree.header()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)  # Name колонка растягивается
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)  # ID колонка может быть изменена пользователем
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Fixed)  # Actions колонка фиксированной ширины

        # Устанавливаем начальные размеры колонок
        self.resultsTree.setColumnWidth(1, 100)  # ID колонка
        self.resultsTree.setColumnWidth(2, 80)  # Actions колонка

        self.resultsTree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(self.resultsTree)

    def display_hierarchical_results(self, objects, is_search_result=False):
        self.resultsTree.clear()

        # Convert to list if single object
        if not isinstance(objects, list):
            objects = [objects]
            is_search_result = True  # Если получен один объект, считаем это результатом поиска

        # Create a dictionary to store all objects by their ID for quick lookup
        objects_dict = {obj['id']: obj for obj in objects}

        # Если это результат поиска, показываем все найденные объекты
        if is_search_result:
            for obj in objects:
                self._add_object_to_tree(obj, objects_dict)
        # Иначе показываем только корневые объекты (с пустым parents)
        else:
            for obj in objects:
                if not obj.get('parents', []):
                    self._add_object_to_tree(obj, objects_dict)

    def _add_object_to_tree(self, obj, objects_dict, parent_item=None):
        # Create tree item
        item = QtWidgets.QTreeWidgetItem([
            str(obj.get('name', 'N/A')),
            str(obj.get('id', 'N/A'))
        ])

        # Add to root if no parent_item, otherwise add as child
        if parent_item is None:
            self.resultsTree.addTopLevelItem(item)
        else:
            parent_item.addChild(item)

        # Create widget for the button
        button_widget = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_widget)
        button_layout.setContentsMargins(4, 0, 4, 0)

        # Create Load button
        load_button = QtWidgets.QPushButton('Load')
        load_button.setProperty('part_id', str(obj.get('id')))
        load_button.clicked.connect(self.handle_load_button)
        button_layout.addWidget(load_button)

        # Set the widget as item widget
        self.resultsTree.setItemWidget(item, 2, button_widget)

        # Recursively add children
        children = obj.get('children', [])
        for child_id in children:
            child_obj = objects_dict.get(child_id)
            if child_obj:
                self._add_object_to_tree(child_obj, objects_dict, item)

    def handle_load_button(self):
        button = self.sender()
        if isinstance(button, QtWidgets.QPushButton):
            part_id = button.property('part_id')
            if part_id:
                self.load_object(part_id)

    def load_object(self, part_id):
        try:
            path_params = {"id": part_id}
            response = send_get_request("/api/basic_object/{id}", path_params=path_params)
            data = json.loads(response)
            print(f"Loaded data for part {part_id}:", data)

            file_path = data.get('bounding_contour', {}).get('brep_files', {}).get('path')

            if file_path:
                QtWidgets.QMessageBox.information(self, 'Success', f'Part found: {file_path}')
                try:
                    import FreeCAD
                    FreeCAD.open(file_path)
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, 'Error', f'Failed to open file in FreeCAD: {str(e)}')
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'Object found, but no file path available!')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while loading the object: {str(e)}')

    def search_part(self):
        part_name = self.textInput.text()
        if not part_name:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please enter a part name!')
            return

        try:
            query_params = {"name": part_name}
            response = send_get_request("/api/basic_object", query_params=query_params)
            data = json.loads(response)

            print("Search response:", data)

            if isinstance(data, dict) and 'error' in data:
                QtWidgets.QMessageBox.critical(self, 'Error', str(data['error']))
                return

            objects = None
            if isinstance(data, list):
                objects = data
            elif isinstance(data, dict):
                if 'basic_object' in data:
                    objects = data['basic_object']
                elif 'basic_objects' in data:
                    objects = data['basic_objects']
                else:
                    objects = [data]

            if objects:
                self.display_hierarchical_results(objects, is_search_result=True)  # Добавлен параметр is_search_result
                self.resultsTree.show()
            else:
                QtWidgets.QMessageBox.information(self, 'Information', 'No objects found with this name!')
                self.resultsTree.clear()

        except Exception as e:
            print(f"Exception in search_part: {str(e)}")
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
            self.resultsTree.clear()

    def find_all_parts(self):
        try:
            response = send_get_request("/api/basic_objects")
            data = json.loads(response)

            if isinstance(data, dict) and 'error' in data:
                QtWidgets.QMessageBox.critical(self, 'Error', str(data['error']))
                return

            objects = None
            if isinstance(data, list):
                objects = data
            elif isinstance(data, dict):
                if 'basic_objects' in data:
                    objects = data['basic_objects']
                elif 'basic_object' in data:
                    objects = data['basic_object']
                else:
                    objects = [data]

            if objects:
                self.display_hierarchical_results(objects,
                                                  is_search_result=False)  # Явно указываем, что это не результат поиска
                self.resultsTree.show()
            else:
                QtWidgets.QMessageBox.information(self, 'Information', 'No objects found!')
                self.resultsTree.clear()

        except Exception as e:
            print(f"Exception in find_all_parts: {str(e)}")
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
            self.resultsTree.clear()