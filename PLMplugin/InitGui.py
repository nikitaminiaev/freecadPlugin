import FreeCAD
import FreeCADGui
from PySide2 import QtWidgets


class MyPlugin:
    def __init__(self):
        self.form = None  # Инициализируем атрибут формы как None

    def Activated(self):
        try:
            from my_dialog import MyDialog
            if self.form is None:  # Если форма еще не создана
                self.form = MyDialog()
            if self.form:  # Проверяем, что форма успешно создана
                self.form.show()
            else:
                FreeCAD.Console.PrintError("Failed to create dialog form\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error creating dialog: {str(e)}\n")

    def GetResources(self):
        return {
            'Pixmap': '',
            'MenuText': 'Open PLM Form',
            'ToolTip': 'Open a custom form with HTTP requests'
        }


FreeCADGui.addCommand('MyFormCommand', MyPlugin())


class MyWorkbench(FreeCADGui.Workbench):
    def __init__(self):
        self.__class__.MenuText = 'PLM'
        self.__class__.ToolTip = 'Custom workbench'
        self.__class__.Icon = ''

    def Initialize(self):
        self.appendToolbar('My Toolbar', ['MyFormCommand'])

    def GetClassName(self):
        return 'Gui::PythonWorkbench'


FreeCADGui.addWorkbench(MyWorkbench())