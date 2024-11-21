from PySide2 import QtWidgets, QtCore

class ObjectTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        headers = ['Name', 'ID', 'Actions']
        self.setColumnCount(len(headers))
        self.setHeaderLabels(headers)

        header = self.header()

        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)

        self.setColumnWidth(0, 240)
        self.setColumnWidth(1, 240)

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

    def display_hierarchical_results(self, objects, is_search_result=False, load_callback=None):
        self.clear()
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

        button_widget = self._create_button_widget(obj.id, load_callback)
        self.setItemWidget(item, 2, button_widget)

        for child_id in obj.children:
            child_obj = objects_dict.get(child_id)
            if child_obj:
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
