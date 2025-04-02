from PySide2 import QtWidgets, QtCore
from models import BasicObject
import json
from utils.logger import log

class ObjectTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api_client = None
        self.load_callback = None  # Добавляем атрибут
        self.setup_ui()
        self.itemExpanded.connect(self.on_item_expanded)

    def setup_ui(self):
        headers = ['Name', 'ID', 'Actions']
        self.setColumnCount(len(headers))
        self.setHeaderLabels(headers)

        header = self.header()

        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        self.setColumnWidth(0, 240)
        self.setColumnWidth(1, 270)

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

    def display_hierarchical_results(self, objects, is_search_result=False, load_callback=None):
        self.clear()
        self.load_callback = load_callback  # Сохраняем callback
        objects_dict = {obj.id: obj for obj in objects}

        if is_search_result:
            for obj in objects:
                self._add_object_to_tree(obj, objects_dict, load_callback=load_callback)
        else:
            for obj in objects:
                if not obj.parents:
                    self._add_object_to_tree(obj, objects_dict, load_callback=load_callback)

    def _add_object_to_tree(self, obj, objects_dict, parent_item=None, load_callback=None):
        item = QtWidgets.QTreeWidgetItem([
            str(obj.name),
            str(obj.id)
        ])

        item.setData(0, QtCore.Qt.UserRole, obj.id)

        if parent_item is None:
            self.addTopLevelItem(item)
        else:
            parent_item.addChild(item)

        # Создаем QLineEdit для отображения имени
        name_line_edit = QtWidgets.QLineEdit(str(obj.name))
        name_line_edit.setReadOnly(True)  # Делаем поле только для чтения
        self.setItemWidget(item, 0, name_line_edit)

        # Создаем QLineEdit для отображения ID
        id_line_edit = QtWidgets.QLineEdit(str(obj.id))
        id_line_edit.setReadOnly(True)  # Делаем поле только для чтения
        self.setItemWidget(item, 1, id_line_edit)

        button_widget = self._create_button_widget(obj.id, load_callback)
        self.setItemWidget(item, 2, button_widget)

        # Рекурсивное добавление дочерних элементов
        for child_id in obj.children:
            child_obj = objects_dict.get(child_id)
            if not child_obj:
                child_obj = BasicObject({
                    'id': child_id,
                    'children': [],
                    'parents': [obj.id]
                })
            self._add_object_to_tree(child_obj, objects_dict, item, load_callback)

    def _create_button_widget(self, part_id, load_callback=None):
        button_widget = QtWidgets.QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_widget)
        button_layout.setContentsMargins(4, 0, 4, 0)

        load_button = QtWidgets.QPushButton('Load')
        load_button.setProperty('part_id', str(part_id))
        if load_callback:
            load_button.clicked.connect(lambda: load_callback(part_id))
        button_layout.addWidget(load_button)

        return button_widget

    def on_item_expanded(self, item):
        # Проверяем, загружены ли уже дети
        if item.data(0, QtCore.Qt.UserRole + 1):  # Используем дополнительную роль для флага
            return
        
        obj_id = item.data(0, QtCore.Qt.UserRole)
        
        # Показываем индикатор загрузки
        loading_item = QtWidgets.QTreeWidgetItem(["Loading...", "", ""])
        item.addChild(loading_item)
        
        try:
            # Получаем данные о детях объекта
            response = self.api_client.send_get_request(
                "/api/basic_objects/{id}/children",
                path_params={"id": obj_id}
            )
            data = json.loads(response)
            children = BasicObject.from_response(data)
            
            # Удаляем индикатор загрузки вместе с остальными дочерними элементами
            item.takeChildren()
            
            # Добавляем новые элементы
            if children:
                objects_dict = {obj.id: obj for obj in children}
                for child in children:
                    self._add_object_to_tree(child, objects_dict, item, self.load_callback)
            
            # Помечаем, что дети загружены
            item.setData(0, QtCore.Qt.UserRole + 1, True)
        except Exception as e:
            item.takeChildren()
            error_item = QtWidgets.QTreeWidgetItem(["Error loading children", "", ""])
            item.addChild(error_item)
            log(f"Error loading children for object {obj_id}: {str(e)}")
