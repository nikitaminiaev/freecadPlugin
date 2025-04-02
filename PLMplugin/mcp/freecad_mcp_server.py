import json
import socket
import traceback
from consts import FREECAD_HOST, FREECAD_PORT
from PySide2 import QtCore, QtWidgets
import FreeCAD as App
import FreeCADGui as Gui
from freecad_executor import FreeCADExecutor

class FreeCADMCPServer:
    def __init__(self, host=FREECAD_HOST, port=FREECAD_PORT):
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.client = None
        self.buffer = b''
        self.timer = None
        self.executor = FreeCADExecutor()
    
    def start(self):
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            self.socket.setblocking(False)
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self._process_server)
            self.timer.start(100)  # 100ms interval
            App.Console.PrintMessage(f"FreeCAD MCP server started on {self.host}:{self.port}\n")
        except Exception as e:
            App.Console.PrintError(f"Failed to start server: {str(e)}\n")
            self.stop()
            
    def stop(self):
        self.running = False
        if self.timer:
            self.timer.stop()
            self.timer = None
        if self.socket:
            self.socket.close()
        if self.client:
            self.client.close()
        self.socket = None
        self.client = None
        App.Console.PrintMessage("FreeCAD MCP server stopped\n")

    def _process_server(self):
        if not self.running:
            return
            
        try:
            if not self.client and self.socket:
                try:
                    self.client, address = self.socket.accept()
                    self.client.setblocking(False)
                    App.Console.PrintMessage(f"Connected to client: {address}\n")
                except BlockingIOError:
                    pass
                except Exception as e:
                    App.Console.PrintError(f"Error accepting connection: {str(e)}\n")
                
            if self.client:
                try:
                    try:
                        data = self.client.recv(1048576)
                        if data:
                            self.buffer += data
                            try:
                                command = json.loads(self.buffer.decode('utf-8'))
                                self.buffer = b''
                                response = self.execute_command(command)
                                response_json = json.dumps(response)
                                self.client.sendall(response_json.encode('utf-8'))
                            except json.JSONDecodeError:
                                pass
                        else:
                            App.Console.PrintMessage("Client disconnected\n")
                            self.client.close()
                            self.client = None
                            self.buffer = b''
                    except BlockingIOError:
                        pass
                    except Exception as e:
                        App.Console.PrintError(f"Error receiving data: {str(e)}\n")
                        self.client.close()
                        self.client = None
                        self.buffer = b''
                        
                except Exception as e:
                    App.Console.PrintError(f"Error with client: {str(e)}\n")
                    if self.client:
                        self.client.close()
                        self.client = None
                    self.buffer = b''
                    
        except Exception as e:
            App.Console.PrintError(f"Server error: {str(e)}\n")

    def execute_command(self, command):
        try:
            cmd_type = command.get("type")
            params = command.get("params", {})
            
            handlers = {
                "run_script": self.handle_run_script,
                "capture_part_view": self.handle_capture_part_view
            }
            
            handler = handlers.get(cmd_type)
            if handler:
                try:
                    App.Console.PrintMessage(f"Executing handler for {cmd_type}\n")
                    result = handler(**params)
                    return {"status": "success", "result": result}
                except Exception as e:
                    App.Console.PrintError(f"Error in handler: {str(e)}\n")
                    traceback.print_exc()
                    return {"status": "error", "message": str(e)}
            else:
                return {"status": "error", "message": f"Unknown command type: {cmd_type}"}
                
        except Exception as e:
            App.Console.PrintError(f"Error executing command: {str(e)}\n")
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def handle_run_script(self, script):
        try:
            # Используем executor для выполнения скрипта
            result = self.executor.execute_code(script, send_result=False)
            return result
        except Exception as e:
            return {
                "success": False,
                "message": "Ошибка при выполнении скрипта",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def handle_capture_part_view(self, part_name, view_type):
        try:
            from mcp.mcp_tools import PartViewCapture
            import os
            
            tmp_dir = '/media/ssd_1_9tb/PycharmProjects/freecadPlugin/tmp'
            
            # Генерируем имя файла с timestamp для уникальности
            import time
            filename = f"{part_name}_{view_type}_{int(time.time())}.png"
            target_path = os.path.join(tmp_dir, filename)
            
            # Получаем изображение
            PartViewCapture.capture_part_view(part_name, view_type, file_path=target_path)
            
            return {
                "success": True,
                "image_data": target_path
            }
        except Exception as e:
            return {
                "success": False,
                "message": "Ошибка при получении скриншота детали",
                "error": str(e),
                "traceback": traceback.format_exc()
            }

class FreeCADMCPPanel:
    def __init__(self):
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("FreeCAD MCP")
        
        layout = QtWidgets.QVBoxLayout(self.form)
        
        # Server status
        self.status_label = QtWidgets.QLabel("Server: Stopped")
        layout.addWidget(self.status_label)
        
        # Start/Stop buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.start_button = QtWidgets.QPushButton("Start Server")
        self.stop_button = QtWidgets.QPushButton("Stop Server")
        self.stop_button.setEnabled(False)
        
        self.start_button.clicked.connect(self.start_server)
        self.stop_button.clicked.connect(self.stop_server)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)
        
        # Server instance
        self.server = None
        
    def start_server(self):
        if not self.server:
            self.server = FreeCADMCPServer()
            self.server.start()
            self.status_label.setText("Server: Running")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
    def stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None
            self.status_label.setText("Server: Stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

def show_panel():
    """Показывает панель управления MCP сервером в интерфейсе FreeCAD"""
    panel = FreeCADMCPPanel()
    Gui.Control.showDialog(panel)
    return panel 