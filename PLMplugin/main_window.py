import json

from PySide2 import QtWidgets, QtCore

from utils.cad_utils import CADUtils, PartCreationDTO, Coordinates
from models import BasicObject
from widgets import ObjectTreeWidget
from api_client import APIClient
from client_panel import PLMClientPanel
from plm_functions import PLMFunctions
from utils.logger import log

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
        
        self.mcp_server = None
        self.toggle_mcp_button = QtWidgets.QPushButton('Start MCP Server')
        self.toggle_mcp_button.clicked.connect(self.toggle_mcp_server)
        count_layout.addWidget(self.toggle_mcp_button)
        
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

        # Checkboxes for is_assembly and is_shell
        self.isAssemblyCheckbox = QtWidgets.QCheckBox('Is Assembly')
        self.isShellCheckbox = QtWidgets.QCheckBox('Is Shell')

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
        search_layout.addWidget(self.isAssemblyCheckbox)
        search_layout.addWidget(self.isShellCheckbox)
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

            is_assembly = self.isAssemblyCheckbox.isChecked()
            is_shell = self.isShellCheckbox.isChecked()
            parent_id = None

            if is_assembly:
                # Сборка не сохраняет BREP напрямую, она берет его из детей Shell
                parent_dto = PartCreationDTO(brep_string=None, label=active_doc.Label)
                if doc_id:
                    parent_dto.id = doc_id
                parent_id = self._upload_single_object(parent_dto, author, None, is_assembly=True, is_shell=False)
                if parent_id:
                    CADUtils.set_id(active_doc, parent_id)
            child_ids = {}
            placements_to_restore = {}
            for selected_obj in selected_objs:
                # Сохраняем координаты и сбрасываем Placement (для не-сборок)
                saved_coordinates = self._extract_and_reset_placement(selected_obj)
                placements_to_restore[selected_obj] = saved_coordinates

                part_dto = CADUtils.create_dto_from_object(selected_obj)
                # Заменяем координаты в DTO на сохранённые (до сброса)
                part_dto.coordinates = saved_coordinates
                if comment and part_dto.label in comment:
                    part_dto.id = comment[part_dto.label]
                
                # Если сохраняем сборку, то все дочерние тела помечаем как Shell
                # В противном случае используем флаги из чекбоксов
                current_is_assembly = False if is_assembly else is_assembly
                current_is_shell = True if is_assembly else is_shell
                
                # Передаем parent_id только если мы в режиме сборки (parent_id задан)
                obj_id = self._upload_single_object(
                    part_dto, 
                    author, 
                    parent_id, 
                    current_is_assembly, 
                    current_is_shell
                )
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

            if is_assembly and parent_id:
                self.plm_functions.save_position(parent_id)

            # Восстанавливаем Placement после сохранения, чтобы объекты остались на месте визуально
            for obj, coords in placements_to_restore.items():
                CADUtils.restore_placement(obj, coords)

        except ImportError:
            QtWidgets.QMessageBox.critical(self, 'Error', 'FreeCAD module not available!')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while uploading: {str(e)}')

    def _upload_single_object(self, part_dto, author, parent_id, is_assembly, is_shell):
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
            "is_shell": is_shell,
            "brep_files": {
                "brep_string": part_dto.brep_string if part_dto.brep_string else ""
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

        if parent_id and parent_id != existing_id:
            payload["parent_id"] = parent_id

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
            
            # Если вернулся список, берем первый элемент
            if isinstance(data, list) and data:
                data = data[0]

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
            QtWidgets.QMessageBox.warning(self, 'Error', f'Error uploading object: {str(e)}')
            return None

    def _extract_and_reset_placement(self, obj) -> Coordinates:
        """Извлекает координаты из Placement объекта и сбрасывает его.

        Args:
            obj: FreeCAD объект

        Returns:
            Coordinates: Сохранённые координаты до сброса
        """
        saved_coordinates = Coordinates(
            x=obj.Placement.Base.x,
            y=obj.Placement.Base.y,
            z=obj.Placement.Base.z,
            angle=obj.Placement.Rotation.Angle,
            axis={
                'x': obj.Placement.Rotation.Axis.x,
                'y': obj.Placement.Rotation.Axis.y,
                'z': obj.Placement.Rotation.Axis.z
            }
        )
        CADUtils.reset_placement(obj)
        return saved_coordinates

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

            if obj_id is None:
                QtWidgets.QMessageBox.information(self, 'Info', 'Please select any object')
                return

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

            last_opened_parent_id = self._get_last_opened_parent_id(parent_ids)
            if last_opened_parent_id:
                self.load_object_in_new_doc(last_opened_parent_id)
                return

            selected_parent_id = self._ask_user_to_select_parent(parent_ids)
            if selected_parent_id is None:
                return

            self.load_object_in_new_doc(selected_parent_id)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred: {str(e)}')

    def _get_last_opened_parent_id(self, parent_ids):
        """Возвращает последнего открытого родителя из списка parent_ids."""
        available_parent_ids = set(parent_ids)
        for opened_id in reversed(self.last_opened_obj_ids):
            if opened_id not in available_parent_ids:
                continue
            return opened_id
        return None

    def _ask_user_to_select_parent(self, parent_ids):
        """Показывает диалог выбора родителя и возвращает его ID."""
        parent_titles = []
        for parent_id in parent_ids:
            parent_name = self._get_object_name_by_id(parent_id)
            parent_title = f"{parent_name} ({parent_id})" if parent_name else str(parent_id)
            parent_titles.append(parent_title)

        selected_parent_title, is_selected = QtWidgets.QInputDialog.getItem(
            self,
            'Выбор родителя',
            'Выберите родительский объект:',
            parent_titles,
            0,
            False
        )
        if not is_selected or not selected_parent_title:
            return None

        selected_index = parent_titles.index(selected_parent_title)
        return parent_ids[selected_index]

    def _get_object_name_by_id(self, obj_id):
        """Возвращает имя объекта по ID для отображения в UI."""
        try:
            response = self.api_client.send_get_request(
                "/api/basic_object/{id}",
                path_params={"id": obj_id}
            )
            data = json.loads(response)
            if isinstance(data, dict):
                return data.get('name')
            return None
        except Exception:
            return None

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

    def load_object_in_new_doc(self, obj_id, child_depths=None, absolute_coordinates=None):
        try:
            log(f"DEBUG load_object_in_new_doc: obj_id={obj_id}")
            log(f"DEBUG load_object_in_new_doc: child_depths={child_depths}")
            log(f"DEBUG load_object_in_new_doc: absolute_coordinates count={len(absolute_coordinates) if absolute_coordinates else 0}")
            
            response = self.api_client.send_get_request(
                "/api/basic_object/{id}",
                path_params={"id": obj_id}
            )
            data = json.loads(response)
            obj = BasicObject.from_response(data)
            
            doc_name = obj.name if obj and obj.name and obj.name != 'N/A' else f"Document_{obj_id}"
            
            CADUtils.close_active_doc()
            active_doc = CADUtils.create_new_doc(doc_name)
            
            # Создаем словарь для быстрого поиска depth по child_id и parent_child_module_id
            child_depths_dict = {}
            if child_depths:
                for cd in child_depths:
                    key = (cd.get('child_id'), cd.get('parent_child_module_id'))
                    child_depths_dict[key] = cd.get('depth', 1)
            
            log(f"DEBUG load_object_in_new_doc: child_depths_dict={child_depths_dict}")
            
            # Создаем словарь absolute_coordinates для быстрого поиска
            absolute_coordinates_dict = self._build_absolute_coordinates_dict(absolute_coordinates or [])
            
            self._load_object(obj_id, depth=1, child_depths_dict=child_depths_dict, absolute_coordinates_dict=absolute_coordinates_dict, is_recursive_call=False)
            CADUtils.recompute_doc()
            CADUtils.set_id(active_doc, obj_id)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while loading the object: {str(e)}')

        self.last_opened_obj_ids.append(obj_id)
    
    def _build_absolute_coordinates_dict(self, absolute_coordinates: list) -> dict:
        """
        Создает словарь для быстрого поиска абсолютных координат.
        
        Структура:
        result[child_id][parent_instance_pcm_key][child_pcm_key] = coordinates
        
        Пример:
        result = {
            '6776e684': {
                'a5153e34': {'4c0a6125': {x:0, z:56}},
                '0273bdc8': {'4c0a6125': {x:41, z:26}}
            },
        }
        """
        result = {}
        for entry in absolute_coordinates:
            obj_id = entry.get("object_id")
            pcm_id = entry.get("parent_child_module_id")
            parent_instance_pcm_id = entry.get("parent_instance_pcm_id")
            
            if not obj_id:
                continue
            
            if obj_id not in result:
                result[obj_id] = {}
            
            parent_instance_key = parent_instance_pcm_id if parent_instance_pcm_id else "root"
            if parent_instance_key not in result[obj_id]:
                result[obj_id][parent_instance_key] = {}

            child_pcm_key = pcm_id if pcm_id else "default"
            result[obj_id][parent_instance_key][child_pcm_key] = entry.get("absolute_coordinates")
        
        return result

    def _apply_placement_from_coordinates(self, cad_obj, coords_dict):
        """Применяет Placement к объекту FreeCAD из словаря координат."""
        if not coords_dict:
            return
        try:
            axis = coords_dict.get("axis", {"x": 0.0, "y": 0.0, "z": 0.0})
            cad_obj.Placement.Base.x = coords_dict.get("x", 0.0)
            cad_obj.Placement.Base.y = coords_dict.get("y", 0.0)
            cad_obj.Placement.Base.z = coords_dict.get("z", 0.0)
            cad_obj.Placement.Rotation.Angle = coords_dict.get("angle", 0.0)
            cad_obj.Placement.Rotation.Axis.x = axis.get("x", 0.0)
            cad_obj.Placement.Rotation.Axis.y = axis.get("y", 0.0)
            cad_obj.Placement.Rotation.Axis.z = axis.get("z", 0.0)
        except Exception as e:
            log(f"Failed to apply placement for {getattr(cad_obj, 'Label', 'unknown')}: {str(e)}")

    def _set_parent_child_module_id(self, cad_obj, parent_child_module_id):
        """Сохраняет ID записи parent_child_module в объекте FreeCAD."""
        if not parent_child_module_id:
            return
        try:
            if not hasattr(cad_obj, "ParentChildModuleId"):
                cad_obj.addProperty("App::PropertyString", "ParentChildModuleId")
            cad_obj.ParentChildModuleId = parent_child_module_id
        except Exception as e:
            log(f"Failed to set ParentChildModuleId for {getattr(cad_obj, 'Label', 'unknown')}: {str(e)}")

    def _attach_to_parent_group(self, parent_obj, child_obj):
        """Добавляет child_obj в Group родителя."""
        if not parent_obj or not child_obj:
            return
        try:
            current_group = list(parent_obj.Group) if hasattr(parent_obj, "Group") else []
            current_group.append(child_obj)
            parent_obj.Group = current_group
        except Exception as e:
            log(f"Failed to attach {getattr(child_obj, 'Label', 'unknown')} to parent group: {str(e)}")

    def _create_link_instance(self, source_obj, label, parent_child_module_id=None, coordinates=None):
        """Создает экземпляр-ссылку App::Link на source_obj."""
        try:
            import FreeCAD as App
            doc = App.ActiveDocument
            link_obj = doc.addObject("App::Link", f"Link_{label}")
            link_obj.setLink(source_obj)
            link_obj.Label = label
            self._set_parent_child_module_id(link_obj, parent_child_module_id)
            self._apply_placement_from_coordinates(link_obj, coordinates)
            return link_obj
        except Exception as e:
            log(f"Failed to create link instance for {label}: {str(e)}")
            return None

    def load_object_in_same_doc(self, obj_id):
        try:
            try:
                CADUtils.get_active_doc()
            except:
                QtWidgets.QMessageBox.critical(self, 'Error', 'no active doc!')
                return

            self._load_object(obj_id, depth=0, child_depths_dict=None, is_recursive_call=False)
            CADUtils.recompute_doc()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Error', f'An error occurred while loading the object: {str(e)}')

        self.last_opened_obj_ids.append(obj_id)

    def _load_object(
        self,
        obj_id,
        depth=1,
        is_recursive_call=False,
        parent_coordinates=None,
        parent_child_module_id=None,
        child_depths_dict=None,
        absolute_coordinates_dict=None,
        parent_container=None
    ):
        response = self.api_client.send_get_request(
            "/api/basic_object/{id}",
            path_params={"id": obj_id}
        )
        data = json.loads(response)
        obj = BasicObject.from_response(data)

        if not obj:
            log(f"Failed to load object with ID: {obj_id}")
            return None

        created_obj = None

        # Сначала загружаем геометрию самого объекта (если есть BREP)
        should_load_geometry = bool(obj.brep_string)
        if should_load_geometry:
            if obj.is_assembly:
                load_context = "recursive" if is_recursive_call else "direct"
                log(f"Assembly {load_context} load: creating part for {obj.name}")
            else:
                log(f"Part load: creating part for {obj.name}")

        if should_load_geometry:
            coordinates = None
            if is_recursive_call:
                if parent_coordinates:
                    coords_dict = parent_coordinates
                    coordinates = Coordinates(
                        x=coords_dict.get("x", 0.0),
                        y=coords_dict.get("y", 0.0),
                        z=coords_dict.get("z", 0.0),
                        angle=coords_dict.get("angle", 0.0),
                        axis=coords_dict.get("axis", {"x": 0.0, "y": 0.0, "z": 0.0})
                    )
                    log(f"Applying coordinates for {obj.name}: {coords_dict}")
                else:
                    log(
                        f"Координаты для рекурсивной загрузки не найдены "
                        f"({obj.name}, id={obj.id}), объект будет загружен без placement (по умолчанию)"
                    )

            part_dto = PartCreationDTO(
                brep_string=obj.brep_string,
                id=obj.id,
                label=obj.name,
                coordinates=coordinates,
                parent_child_module_id=parent_child_module_id
            )

            created_obj = CADUtils.create_part_with_brep(part_dto)
            self._attach_to_parent_group(parent_container, created_obj)
        else:
            log(f"Skipping object {obj.name} (ID: {obj_id}) - no BREP data")

        # Для сборок без собственного BREP создаем пустой контейнер,
        # чтобы сохранять вложенную иерархию в документе.
        if created_obj is None and obj.is_assembly:
            try:
                import FreeCAD as App
                doc = App.ActiveDocument
                created_obj = doc.addObject('App::Part', obj.name)
                self._set_parent_child_module_id(created_obj, parent_child_module_id)
                self._apply_placement_from_coordinates(created_obj, parent_coordinates)
                self._attach_to_parent_group(parent_container, created_obj)
                log(f"Created assembly container for {obj.name} without BREP")
            except Exception as e:
                log(f"Failed to create assembly container for {obj.name}: {str(e)}")

        # Потом загружаем детей (если это сборка)
        if obj.is_assembly and obj.children_with_coordinates:
            log(f"Loading assembly {obj.name} with {len(obj.children_with_coordinates)} children")
            created_children_by_key = {}
            for child_entry in obj.children_with_coordinates:
                child_id = child_entry["child_id"]
                child_pcm_id = child_entry.get("parent_child_module_id")
                
                child_depth = depth
                if child_depths_dict:
                    key = (child_id, child_pcm_id)
                    if key in child_depths_dict:
                        child_depth = child_depths_dict[key]
                
                if child_depth > 0:
                    # Для вложенной структуры в Group используем локальные координаты
                    # связи parent->child (из children_with_coordinates).
                    child_relative_coords = child_entry.get("coordinates") or None

                    # На одном уровне повторные child_id создаем через App::Link на первый объект.
                    cache_key = (child_id, child_depth)
                    if cache_key in created_children_by_key:
                        source_obj = created_children_by_key[cache_key]
                        link_obj = self._create_link_instance(
                            source_obj=source_obj,
                            label=getattr(source_obj, "Label", obj.name),
                            parent_child_module_id=child_pcm_id,
                            coordinates=child_relative_coords,
                        )
                        self._attach_to_parent_group(created_obj, link_obj)
                        continue

                    child_obj = self._load_object(
                        child_id,
                        depth=child_depth - 1,
                        is_recursive_call=True,
                        parent_coordinates=child_relative_coords,
                        parent_child_module_id=child_pcm_id,
                        child_depths_dict=child_depths_dict,
                        absolute_coordinates_dict=absolute_coordinates_dict,
                        parent_container=created_obj
                    )
                    if child_obj is not None:
                        created_children_by_key[cache_key] = child_obj
                else:
                    log(f"Skipping child {child_id} (depth=0)")

        return created_obj

    def toggle_mcp_server(self):
        """Включает или выключает MCP сервер"""
        try:
            if not self.mcp_server:
                # Импортируем только при необходимости
                from mcp.freecad_mcp_server import FreeCADMCPServer
                self.mcp_server = FreeCADMCPServer()
                self.mcp_server.start()
                self.toggle_mcp_button.setText('Stop MCP Server')
                log("MCP сервер запущен")
            else:
                self.mcp_server.stop()
                self.mcp_server = None
                self.toggle_mcp_button.setText('Start MCP Server')
                log("MCP сервер остановлен")
        except Exception as e:
            log(f"Ошибка при управлении MCP сервером: {str(e)}")
            QtWidgets.QMessageBox.warning(
                self, 'MCP Server Error', f'Произошла ошибка: {str(e)}'
            )