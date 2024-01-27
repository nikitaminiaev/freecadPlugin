import FreeCADGui
# from PyQt4 import QtCore
from PySide2 import QtCore, QtWidgets

# Класс MyPlugin() наследуется от класса FreeCADBase.Base
class MyPlugin(QtWidgets.QDockWidget):

    def __init__(self):
        super(MyPlugin, self).__init__()
        print('activated12')
        self.panel = FreeCADGui.PySideUic.loadUi("/home/nekit/snap/freecad/common/Mod/Plugindb/myPlugin.ui", self)
        print('activated18')
        # Привязываем обработчики событий к кнопкам
        self.panel.button1.clicked.connect(self.on_button1_clicked)
        self.panel.button2.clicked.connect(self.on_button2_clicked)

    def on_button1_clicked(self):
        print("Hello, world!")

    def on_button2_clicked(self):
        print("Hello0000 2")
