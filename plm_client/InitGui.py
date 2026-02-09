import FreeCAD
import FreeCADGui


class PLMClientPlugin:
    def __init__(self):
        self.form = None  # Инициализируем атрибут формы как None

    def Activated(self):
        try:
            from client_window import PLMClientWindow
            if self.form is None:  # Если форма еще не создана
                self.form = PLMClientWindow()
            if self.form:  # Проверяем, что форма успешно создана
                self.form.show()
            else:
                FreeCAD.Console.PrintError("Не удалось создать форму диалога\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"Ошибка при создании диалога: {str(e)}\n")

    def GetResources(self):
        return {
            'Pixmap': '',
            'MenuText': 'Открыть PLM Client',
            'ToolTip': 'Открыть клиент для WebSocket соединения'
        }


FreeCADGui.addCommand('PLMClientCommand', PLMClientPlugin())


class PLMClientWorkbench(FreeCADGui.Workbench):
    def __init__(self):
        self.__class__.MenuText = 'PLM Client'
        self.__class__.ToolTip = 'WebSocket клиент для PLM'
        self.__class__.Icon = ''

    def Initialize(self):
        self.appendToolbar('PLM Client', ['PLMClientCommand'])

    def GetClassName(self):
        return 'Gui::PythonWorkbench'


FreeCADGui.addWorkbench(PLMClientWorkbench()) 