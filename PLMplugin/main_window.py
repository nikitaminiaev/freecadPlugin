import json

from PySide2 import QtWidgets

from cad_utils import CADUtils, PartCreationDTO, Coordinates
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
        self.uploadActiveButton = QtWidgets.QPushButton('Save')

        self.submitButton.clicked.connect(self.search_part)
        self.findAllButton.clicked.connect(self.find_all_parts)
        self.uploadActiveButton.clicked.connect(self.upload_active_part)

        search_layout.addWidget(self.label)
        search_layout.addWidget(self.textInput)
        search_layout.addWidget(self.submitButton)
        search_layout.addWidget(self.findAllButton)
        search_layout.addWidget(self.uploadActiveButton)
        layout.addLayout(search_layout)

        # Tree widget
        self.resultsTree = ObjectTreeWidget()
        layout.addWidget(self.resultsTree)

    def upload_active_part(self):
        """Upload currently active file to the server"""
        try:
            active_doc = CADUtils.get_active_doc()
            author = active_doc.CreatedBy.encode().decode('utf-8')

            selected_objs = CADUtils.get_all_selected_obj()
            if not selected_objs:
                QtWidgets.QMessageBox.warning(self, 'Warning', 'No object selected in FreeCAD!')
                return
            selected_obj = selected_objs[0]
            part_dto = CADUtils.create_dto_from_object(selected_obj)
            label = part_dto.label.encode().decode('utf-8')

            payload = {
                "is_assembly": False,  # You might want to detect this automatically
                "brep_files": {
                    "brep_string": part_dto.brep_string
                },
                "name": part_dto.label,
                "author": author,
                "description": f"Uploaded from FreeCAD: {label}",
                "coordinates": {
                    "x": part_dto.coordinates.x,
                    "y": part_dto.coordinates.y,
                    "z": part_dto.coordinates.z,
                    "angle": part_dto.coordinates.angle,
                    "axis": part_dto.coordinates.axis
                },
                "role": "uploaded_part",
                "role_description": "Part uploaded from active FreeCAD document"
            }
            # Проверяем, существует ли уже объект с таким ID
            existing_id = part_dto.id

            if existing_id:  # Проверяем только если есть ID
                try:
                    self.api_client.send_get_request(
                        "/api/basic_object/{id}",
                        path_params={"id": existing_id}
                    )
                    # Если объект существует, используем PATCH запрос
                    response = self.api_client.send_patch_request(
                        f"/api/basic_object/{existing_id}",
                        payload
                    )
                except Exception:
                    # Если получили 404 или другую ошибку при поиске, создаем новый объект
                    response = self.api_client.send_post_request(
                        "/api/basic_object/",
                        payload
                    )
            else:
                # Если ID нет, сразу создаем новый объект
                response = self.api_client.send_post_request(
                    "/api/basic_object/",
                    payload
                )

            data = json.loads(response)
            print(data)
            if isinstance(data, dict):
                if 'error' in data:
                    QtWidgets.QMessageBox.critical(self, 'Error', str(data['error']))
                    return

                if 'id' not in data:
                    QtWidgets.QMessageBox.critical(self, 'Error', 'Server response missing object ID')
                    return

                try:
                    CADUtils.save_id(active_doc, data['id'])
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, 'Warning',
                                                  f'File uploaded but failed to save ID to document: {str(e)}')

        except ImportError:
            QtWidgets.QMessageBox.critical(self, 'Error', 'FreeCAD module not available!')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while uploading: {str(e)}')

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

            if obj.brep_string:
                active_doc = CADUtils.get_active_doc()
                if not active_doc:
                    CADUtils.create_new_doc(f"Document_{part_id}")

                part_dto = PartCreationDTO(
                    brep_string=obj.brep_string,
                    id=obj.id,
                    label=obj.name,
                    coordinates=Coordinates(
                        x=obj.coordinates["x"],
                        y=obj.coordinates["y"],
                        z=obj.coordinates["z"],
                        angle=obj.coordinates["angle"],
                        axis=obj.coordinates["axis"]
                    )
                )

                CADUtils.create_part_with_brep(part_dto)
            else:
                QtWidgets.QMessageBox.critical(self, 'Error', 'Object found, but no BREP data available!')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while loading the object: {str(e)}')