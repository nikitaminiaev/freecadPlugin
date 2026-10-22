import FreeCAD
import FreeCADGui
from PySide2 import QtCore

# Единый экземпляр главного окна плагина.
# Создаётся при старте FreeCAD (скрыто) — клиентская панель и автоподключение
# WebSocket стартуют сразу; команда "Open PLM Form" просто показывает окно.
_hidden_window = None


def _create_hidden_window():
    """Создаёт окно плагина при старте FreeCAD (без показа).

    Вызывается по QTimer — после запуска GUI event loop, чтобы не трогать
    виджеты во время загрузки модулей."""
    global _hidden_window
    if _hidden_window is not None:
        return
    try:
        from main_window import PLMMainWindow
        _hidden_window = PLMMainWindow()
        _hidden_window.hide()
    except Exception as e:
        FreeCAD.Console.PrintError(f"PLM autostart: {str(e)}\n")


QtCore.QTimer.singleShot(0, _create_hidden_window)


class MyPlugin:
    def __init__(self):
        self.form = None  # Инициализируем атрибут формы как None

    def Activated(self):
        global _hidden_window
        try:
            # Показываем единый экземпляр (создан при старте FreeCAD или сейчас)
            if _hidden_window is None:
                from main_window import PLMMainWindow
                _hidden_window = PLMMainWindow()
            self.form = _hidden_window
            if self.form:
                self.form.show()
            else:
                FreeCAD.Console.PrintError("Failed to create dialog form\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error creating dialog: {str(e)}\n")

    def GetResources(self):
        return {
            'Pixmap': '',
            'MenuText': 'Open PLM Form',
            'ToolTip': 'Open a custom form with HTTP requests and WebSocket client'
        }


try:
    FreeCADGui.addCommand('MyFormCommand', MyPlugin())
except Exception as e:
    FreeCAD.Console.PrintError(f"PLM addCommand: {str(e)}\n")


class MyWorkbench(FreeCADGui.Workbench):
    def __init__(self):
        self.__class__.MenuText = 'PLM'
        self.__class__.ToolTip = 'PLM integration with WebSocket client support'
        self.__class__.Icon = ''

    def Initialize(self):
        self.appendToolbar('My Toolbar', ['MyFormCommand'])
        self.appendMenu('PLM', ['MyFormCommand'])

    def GetClassName(self):
        return 'Gui::PythonWorkbench'


try:
    FreeCADGui.addWorkbench(MyWorkbench())
except Exception as e:
    # Уже зарегистрирован (например, другой копией плагина в Mod/) — не фатально
    FreeCAD.Console.PrintError(f"PLM addWorkbench: {str(e)}\n")
