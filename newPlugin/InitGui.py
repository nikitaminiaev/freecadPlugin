import FreeCAD
import FreeCADGui
from PySide2 import QtWidgets

print(0)
class MyPlugin:
    def Activated(self):
        # Откроем окно формы
        from my_dialog import MyDialog
        form = MyDialog()
        form.exec_()

    def GetResources(self):
        return {
            'Pixmap': '',  # Здесь можно указать путь к иконке кнопки
            'MenuText': 'Open My Form',
            'ToolTip': 'Open a custom form with HTTP requests'
        }
print(1)
FreeCADGui.addCommand('MyFormCommand', MyPlugin())
print(2)
class MyWorkbench(FreeCADGui.Workbench):
    def __init__(self):
        self.__class__.MenuText = 'MyWorkbench'
        self.__class__.ToolTip = 'Custom workbench'
        self.__class__.Icon = ''  # Опционально добавить иконку рабочего стола

    def Initialize(self):
        # Добавим кнопку в панель инструментов
        self.appendToolbar('My Toolbar', ['MyFormCommand'])

    def GetClassName(self):
        return 'Gui::PythonWorkbench'

FreeCADGui.addWorkbench(MyWorkbench())
