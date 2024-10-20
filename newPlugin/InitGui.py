import FreeCAD
import FreeCADGui
from PySide2 import QtWidgets


class MyPlugin:
    def Activated(self):
        from my_dialog import MyDialog
        form = MyDialog()
        form.exec_()

    def GetResources(self):
        return {
            'Pixmap': '',  # Здесь можно указать путь к иконке кнопки
            'MenuText': 'Open PLM Form',
            'ToolTip': 'Open a custom form with HTTP requests'
        }


FreeCADGui.addCommand('MyFormCommand', MyPlugin())


class MyWorkbench(FreeCADGui.Workbench):
    def __init__(self):
        self.__class__.MenuText = 'PLM'
        self.__class__.ToolTip = 'Custom workbench'
        self.__class__.Icon = ''  # Опционально добавить иконку рабочего стола

    def Initialize(self):
        # Добавим кнопку в панель инструментов
        self.appendToolbar('My Toolbar', ['MyFormCommand'])

    def GetClassName(self):
        return 'Gui::PythonWorkbench'


FreeCADGui.addWorkbench(MyWorkbench())
