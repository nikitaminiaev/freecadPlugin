from my_plugin import MyPlugin
import FreeCADGui
from PySide2 import QtCore

# def run():
# Создаем экземпляр плагина
print('Hello1')
plugin = MyPlugin()

# Активируем плагин

FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.BottomDockWidgetArea, plugin)



# if __name__ == "__main__":
#     run()
