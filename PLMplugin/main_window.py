import json

from PySide2 import QtWidgets, QtCore

from cad_utils import CADUtils, PartCreationDTO, Coordinates
from models import BasicObject
from widgets import ObjectTreeWidget
from api_client import APIClient
from client_panel import PLMClientPanel
from plm_functions import PLMFunctions
from logger import log

class PLMMainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.last_opened_obj_ids = []
        self.api_client = APIClient()
        self.client_panel = None  # Панель клиента WebSocket
        self.is_client_panel_visible = False
        self.plm_functions = PLMFunctions(self)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle('PLM')
        self.setGeometry(100, 100, 600, 400)

        # Создаем разделитель для основного окна и клиентской панели
        self.main_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # Создаем контейнер для основных элементов PLM
        self.main_container = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(self.main_container)
        
        # Count display area
        count_layout = QtWidgets.QHBoxLayout()
        self.count_label = QtWidgets.QLabel('Total objects:')
        self.count_display = QtWidgets.QLabel('NaN')
        count_layout.addWidget(self.count_label)
        count_layout.addWidget(self.count_display)
        count_layout.addStretch()
        main_layout.addLayout(count_layout)
        self.update_objects_count()  # Вызываем метод сразу после создания виджетов

        # Search area
        search_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel('Enter Obj Name:')
        self.textInput = QtWidgets.QLineEdit()
        
        # Добавляем поля для limit и offset
        limit_layout = QtWidgets.QHBoxLayout()
        self.limit_label = QtWidgets.QLabel('Limit:')
        self.limit_input = QtWidgets.QLineEdit('10')  # значение по умолчанию
        self.offset_label = QtWidgets.QLabel('Offset:')
        self.offset_input = QtWidgets.QLineEdit('0')  # значение по умолчанию
        
        limit_layout.addWidget(self.limit_label)
        limit_layout.addWidget(self.limit_input)
        limit_layout.addWidget(self.offset_label)
        limit_layout.addWidget(self.offset_input)
        
        self.submitButton = QtWidgets.QPushButton('Search')
        self.findAllButton = QtWidgets.QPushButton('Find All')
        self.uploadActiveButton = QtWidgets.QPushButton('Save')

        # New buttons
        self.goToSupersystemButton = QtWidgets.QPushButton('To Supersystem')
        self.goToSubsystemButton = QtWidgets.QPushButton('To Subsystem')
        self.loadInCurrentDocButton = QtWidgets.QPushButton('Load to Current Doc')
        
        # Добавляем кнопку для отображения/скрытия клиентской панели
        self.toggleClientPanelButton = QtWidgets.QPushButton('WebSocket Client')
        self.toggleClientPanelButton.clicked.connect(self.toggle_client_panel)

        # Connect new buttons to methods
        self.goToSupersystemButton.clicked.connect(self.go_to_supersystem)
        self.goToSubsystemButton.clicked.connect(self.go_to_subsystem)
        self.loadInCurrentDocButton.clicked.connect(self.load_in_current_doc)

        self.submitButton.clicked.connect(self.search_part)
        self.findAllButton.clicked.connect(self.find_all_parts)
        self.uploadActiveButton.clicked.connect(self.upload_active_part)

        search_layout.addWidget(self.label)
        search_layout.addWidget(self.textInput)
        search_layout.addWidget(self.submitButton)
        search_layout.addWidget(self.findAllButton)
        search_layout.addWidget(self.uploadActiveButton)
        search_layout.addWidget(self.goToSupersystemButton)
        search_layout.addWidget(self.goToSubsystemButton)
        search_layout.addWidget(self.loadInCurrentDocButton)
        search_layout.addWidget(self.toggleClientPanelButton)  # Добавляем кнопку клиента
        main_layout.addLayout(search_layout)
        main_layout.addLayout(limit_layout)  # Добавляем новый layout после search_layout

        # Tree widget
        self.resultsTree = ObjectTreeWidget()
        self.resultsTree.api_client = self.api_client
        main_layout.addWidget(self.resultsTree)
        
        # Добавляем основной контейнер в разделитель
        self.main_splitter.addWidget(self.main_container)
        
        # Создаем основной layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.main_splitter)

    def toggle_client_panel(self):
        """Включает/выключает отображение панели клиента WebSocket"""
        if self.is_client_panel_visible:
            # Скрываем панель
            if self.client_panel:
                self.client_panel.hide()
                # Удаляем панель из разделителя
                self.main_splitter.widget(1).setParent(None)
                self.is_client_panel_visible = False
                self.toggleClientPanelButton.setText('WebSocket Client')
        else:
            # Создаем панель, если она еще не создана
            if not self.client_panel:
                self.client_panel = PLMClientPanel()
                # Передаем функции PLM в панель клиента
                self.client_panel.set_plm_functions(self.plm_functions)
            
            # Добавляем панель к разделителю
            self.main_splitter.addWidget(self.client_panel)
            self.client_panel.show()
            self.is_client_panel_visible = True
            self.toggleClientPanelButton.setText('Close Client')
            
            # Устанавливаем соотношение размеров частей разделителя
            self.main_splitter.setSizes([int(self.width() * 0.6), int(self.width() * 0.4)])

    def update_objects_count(self):
        """Update the total objects count display"""
        try:
            count_response = self.api_client.send_get_request("/api/basic_objects/count")
            try:
                count = json.loads(count_response)
                self.count_display.setText(str(count))
            except:
                self.count_display.setText('NaN')
        except:
            self.count_display.setText('NaN')

    def upload_active_part(self):
        """Upload currently active file to the server"""
        try:
            active_doc = CADUtils.get_active_doc()
            author = active_doc.CreatedBy.encode().decode('utf-8')
            doc_id = getattr(active_doc, 'Id', None)
            comment_str = getattr(active_doc, 'Comment', None)
            comment = json.loads(comment_str) if comment_str else {}
            selected_objs = CADUtils.get_all_selected_obj()

            if not selected_objs:
                QtWidgets.QMessageBox.warning(self, 'Warning', 'No object selected in FreeCAD!')
                return
            
            is_assembly = len(selected_objs) > 1
            parrent_id = None

            if is_assembly:
                parrent_dto = PartCreationDTO(brep_string=CADUtils.get_combined_brep_from_objects(selected_objs), label=active_doc.Label)
                if doc_id:
                    parrent_dto.id = doc_id
                parrent_id = self._upload_single_object(parrent_dto, author, None, is_assembly)
                if parrent_id:
                    CADUtils.set_id(active_doc, parrent_id)
            child_ids = {}
            for selected_obj in selected_objs:
                part_dto = CADUtils.create_dto_from_object(selected_obj)
                if comment:
                    part_dto.id = comment[part_dto.label]
                obj_id = self._upload_single_object(part_dto, author, getattr(active_doc, 'Id', None), is_assembly)
                try:
                    if hasattr(selected_obj, 'Id'):
                        selected_obj.Id = obj_id
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, 'Warning',
                                              f'File uploaded but failed to save ID to document: {str(e)}')
                if obj_id:
                    child_ids[part_dto.label] = obj_id
                    
            if child_ids:
                active_doc.Comment = json.dumps(child_ids)

        except ImportError:
            QtWidgets.QMessageBox.critical(self, 'Error', 'FreeCAD module not available!')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while uploading: {str(e)}')

    def _upload_single_object(self, part_dto, author, parent_id, is_assembly):
        """Upload a single object and return its ID"""
        label = part_dto.label.encode().decode('utf-8')
        
        # Добавляем безопасную обработку координат
        coordinates = {
            "x": getattr(part_dto.coordinates, 'x', 0.0) or 0.0,
            "y": getattr(part_dto.coordinates, 'y', 0.0) or 0.0,
            "z": getattr(part_dto.coordinates, 'z', 0.0) or 0.0,
            "angle": getattr(part_dto.coordinates, 'angle', 0.0) or 0.0,
            "axis": getattr(part_dto.coordinates, 'axis', {"x": 0.0, "y": 0.0, "z": 0.0}) or {"x": 0.0, "y": 0.0, "z": 0.0}
        }

        payload = {
            "is_assembly": is_assembly,
            "brep_files": {
                "brep_string": part_dto.brep_string
            },
            "name": label,
            "author": author,
            "description": f"Uploaded from FreeCAD: {label}",
            "coordinates": coordinates,  # Используем обработанные координаты
            "role": "uploaded_part",
            "role_description": "Part uploaded from active FreeCAD document"
        }

        if parent_id:
            payload["parent_id"] = parent_id

        existing_id = part_dto.id

        try:
            if existing_id:
                try:
                    self.api_client.send_get_request(
                        "/api/basic_object/{id}",
                        path_params={"id": existing_id}
                    )
                    response = self.api_client.send_patch_request(
                        f"/api/basic_object/{existing_id}",
                        payload
                    )
                except Exception:
                    response = self.api_client.send_post_request(
                        "/api/basic_object/",
                        payload
                    )
            else:
                response = self.api_client.send_post_request(
                    "/api/basic_object/",
                    payload
                )

            data = json.loads(response)
            if isinstance(data, dict):
                if 'error' in data:
                    QtWidgets.QMessageBox.critical(self, 'Error', str(data['error']))
                    return None

                if 'id' not in data:
                    QtWidgets.QMessageBox.critical(self, 'Error', 'Server response missing object ID')
                    return None

                return data['id']
            return None
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'Error uploading object: {str(e)}')
            return None

    def search_part(self):
        part_name = self.textInput.text()
        if not part_name:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please enter a part name!')
            return

        try:
            response = self.api_client.send_get_request("/api/basic_object", query_params={"name": part_name})
            data = json.loads(response)

            if isinstance(data, dict):
                error_msg = data.get('error') or data.get('error_message')
                if error_msg:
                    QtWidgets.QMessageBox.critical(self, 'Ошибка', str(error_msg))
                    return

            objects = BasicObject.from_response(data)
            if objects:
                self.resultsTree.display_hierarchical_results(
                    objects if isinstance(objects, list) else [objects],
                    is_search_result=True,
                    load_callback=self.load_object_in_new_doc
                )
            else:
                self.resultsTree.clear()

        except Exception as e:
            log(f"Exception in search_part: {str(e)}")
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
            self.resultsTree.clear()

    def find_all_parts(self):
        try:
            # Получаем значения из полей ввода
            try:
                limit = int(self.limit_input.text())
                offset = int(self.offset_input.text())
            except ValueError:
                # Если введены некорректные значения, используем значения по умолчанию
                limit = 10
                offset = 0
                self.limit_input.setText(str(limit))
                self.offset_input.setText(str(offset))
                QtWidgets.QMessageBox.warning(self, 'Warning', 'Invalid limit/offset values. Using defaults.')

            response = self.api_client.send_get_request("/api/basic_objects/top_level", 
                                                      query_params={"limit": limit, "offset": offset})
            data = json.loads(response)

            if isinstance(data, dict) and 'error' in data:
                QtWidgets.QMessageBox.critical(self, 'Error', str(data['error']))
                return

            objects = BasicObject.from_response(data)
            if objects:
                self.resultsTree.display_hierarchical_results(
                    objects,
                    is_search_result=False,
                    load_callback=self.load_object_in_new_doc
                )
            else:
                self.resultsTree.clear()

        except Exception as e:
            log(f"Exception in find_all_parts: {str(e)}")
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')
            self.resultsTree.clear()

    def go_to_subsystem(self):
        try:
            try:
                CADUtils.get_active_doc()
                obj_id = CADUtils.get_all_selected_obj()[0].Id
            except:
                obj_id = self.get_object_id_from_plm_select()

            if obj_id is None:
                QtWidgets.QMessageBox.information(self, 'Info', 'Please select any object')
                return

            self.load_object_in_new_doc(obj_id)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')

    def go_to_supersystem(self):
        try:
            try:
                CADUtils.get_active_doc()
                obj_id = CADUtils.get_all_selected_obj()[0].Id
            except:
                obj_id = self.get_object_id_from_plm_select()

            # Fetch the parents of the object
            response = self.api_client.send_get_request(
                "/api/basic_object/{id}/parent_ids",
                path_params={"id": obj_id}
            )
            parent_ids = json.loads(response)

            if not parent_ids or len(parent_ids) == 0:
                QtWidgets.QMessageBox.information(self, 'Info', 'No parents found for this object.')
                return

            if len(parent_ids) == 1:
                self.load_object_in_new_doc(parent_ids[0])
                return

            for parent_id in parent_ids:
                if parent_id in self.last_opened_obj_ids:
                    self.load_object_in_new_doc(parent_id)
                    return

            #todo далее кейс когда надо показывать окно с выбором парента

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')

    def get_object_id_from_plm_select(self):
        selected_objects = self.resultsTree.selectedItems()
        if not selected_objects:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please select an object first!')
            return None
        selected_item = selected_objects[0]
        obj_id = selected_item.data(0, QtCore.Qt.UserRole)

        return obj_id

    def load_in_current_doc(self):
        try:
            obj_id = self.get_object_id_from_plm_select()
            if obj_id is None:
                QtWidgets.QMessageBox.critical(self, 'Info', f'Please select any object')
            # CADUtils.get_active_doc()
            self.load_object_in_same_doc(obj_id)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')

    def load_object_in_new_doc(self, obj_id):
        try:
            CADUtils.close_active_doc()
            active_doc = CADUtils.create_new_doc(f"Document_{obj_id}")

            self._load_object(obj_id)
            CADUtils.recompute_doc()
            CADUtils.set_id(active_doc, obj_id)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while loading the object: {str(e)}')

        self.last_opened_obj_ids.append(obj_id)

    def load_object_in_same_doc(self, obj_id):
        try:
            try:
                CADUtils.get_active_doc()
            except:
                QtWidgets.QMessageBox.critical(self, 'Error', 'no active doc!')
                return

            self._load_object(obj_id)
            CADUtils.recompute_doc()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while loading the object: {str(e)}')

        self.last_opened_obj_ids.append(obj_id)

    def _load_object(self, obj_id, max_depth=1):
        response = self.api_client.send_get_request(
            "/api/basic_object/{id}",
            path_params={"id": obj_id}
        )
        data = json.loads(response)
        obj = BasicObject(data)

        if max_depth > 0 and hasattr(obj, 'children') and obj.children:
            for child_id in obj.children:
                self._load_object(child_id, max_depth - 1)
            return

        if obj.brep_string:
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