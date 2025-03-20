import traceback
from function_registry import FunctionRegistry
from logger import log

class PLMFunctions:
    """
    Класс с функциями для работы с PLM, которые можно регистрировать в FunctionRegistry.
    Содержит обертки для методов PLMMainWindow.
    """
    
    def __init__(self, main_window=None):
        """
        Инициализация с ссылкой на экземпляр PLMMainWindow
        
        Args:
            main_window: Экземпляр PLMMainWindow
        """
        self.main_window = main_window
    
    def set_main_window(self, main_window):
        """
        Установка ссылки на экземпляр PLMMainWindow
        
        Args:
            main_window: Экземпляр PLMMainWindow
        """
        self.main_window = main_window
        log(f"PLMFunctions: Установлена ссылка на главное окно")
    
    def register_functions(self, function_registry: FunctionRegistry):
        """
        Регистрирует все функции PLM в реестре
        
        Args:
            function_registry: Экземпляр класса FunctionRegistry
        """
        if not self.main_window:
            log("PLMFunctions: Главное окно не задано, функции не будут зарегистрированы")
            return
            
        # Регистрируем функции для работы с PLM
        function_registry.register_function("load_object_in_new_doc", self.load_object_in_new_doc)
        function_registry.register_function("load_object_in_same_doc", self.load_object_in_same_doc)
        function_registry.register_function("search_part", self.search_part)
        function_registry.register_function("find_all_parts", self.find_all_parts)
        function_registry.register_function("go_to_supersystem", self.go_to_supersystem)
        function_registry.register_function("go_to_subsystem", self.go_to_subsystem)
        function_registry.register_function("upload_active_part", self.upload_active_part)
        
        log("PLMFunctions: Функции PLM успешно зарегистрированы")
    
    # Обертки для методов PLMMainWindow
    
    def load_object_in_new_doc(self, obj_id):
        """
        Загружает объект в новый документ FreeCAD
        
        Args:
            obj_id (str): ID объекта для загрузки
        
        Returns:
            dict: Результат операции
        """
        if not self.main_window:
            return {"success": False, "error": "Главное окно не инициализировано"}
        
        try:
            log(f"PLMFunctions: Вызов load_object_in_new_doc с ID: {obj_id}")
            self.main_window.load_object_in_new_doc(obj_id)
            return {
                "success": True,
                "message": f"object {obj_id} successfully loaded in a new document"
            }
        except Exception as e:
            error_msg = f"Error loading object in a new document: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            return {"success": False, "error": str(e)}
    
    def load_object_in_same_doc(self, obj_id):
        """
        Загружает объект в текущий документ FreeCAD
        
        Args:
            obj_id (str): ID объекта для загрузки
        
        Returns:
            dict: Результат операции
        """
        if not self.main_window:
            return {"success": False, "error": "Главное окно не инициализировано"}
        
        try:
            log(f"PLMFunctions: Вызов load_object_in_same_doc с ID: {obj_id}")
            self.main_window.load_object_in_same_doc(obj_id)
            return {
                "success": True,
                "message": f"object {obj_id} successfully loaded in the current document"
            }
        except Exception as e:
            error_msg = f"Error loading object in the current document: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            return {"success": False, "error": str(e)}
    
    def search_part(self, part_name):
        """
        Поиск деталей по имени
        
        Args:
            part_name (str): Имя детали для поиска
        
        Returns:
            dict: Результат операции
        """
        if not self.main_window:
            return {"success": False, "error": "Главное окно не инициализировано"}
        
        try:
            log(f"PLMFunctions: Вызов search_part с именем: {part_name}")
            # Устанавливаем значение в текстовое поле поиска
            self.main_window.textInput.setText(part_name)
            # Вызываем метод поиска
            self.main_window.search_part()
            return {
                "success": True,
                "message": f"search by name '{part_name}' completed"
            }
        except Exception as e:
            error_msg = f"Error searching for a part: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            return {"success": False, "error": str(e)}
    
    def find_all_parts(self, limit=10, offset=0):
        """
        Поиск всех деталей с ограничением и смещением
        
        Args:
            limit (int): Максимальное количество результатов
            offset (int): Смещение результатов
        
        Returns:
            dict: Результат операции
        """
        if not self.main_window:
            return {"success": False, "error": "Главное окно не инициализировано"}
        
        try:
            log(f"PLMFunctions: Вызов find_all_parts с limit: {limit}, offset: {offset}")
            # Устанавливаем значения в поля limit и offset
            self.main_window.limit_input.setText(str(limit))
            self.main_window.offset_input.setText(str(offset))
            # Вызываем метод поиска всех деталей
            self.main_window.find_all_parts()
            return {
                "success": True,
                "message": f"search all parts completed (limit: {limit}, offset: {offset})"
            }
        except Exception as e:
            error_msg = f"Error searching for all parts: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            return {"success": False, "error": str(e)}
    
    def go_to_supersystem(self):
        """
        Переход к суперсистеме
        
        Returns:
            dict: Результат операции
        """
        if not self.main_window:
            return {"success": False, "error": "Главное окно не инициализировано"}
        
        try:
            log("PLMFunctions: Вызов go_to_supersystem")
            self.main_window.go_to_supersystem()
            return {
                "success": True,
                "message": "Navigation to supersystem completed"
            }
        except Exception as e:
            error_msg = f"Ошибка при переходе к суперсистеме: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            return {"success": False, "error": str(e)}
    
    def go_to_subsystem(self):
        """
        Переход к подсистеме
        
        Returns:
            dict: Результат операции
        """
        if not self.main_window:
            return {"success": False, "error": "Главное окно не инициализировано"}
        
        try:
            log("PLMFunctions: Вызов go_to_subsystem")
            self.main_window.go_to_subsystem()
            return {
                "success": True,
                "message": "Navigation to subsystem completed"
            }
        except Exception as e:
            error_msg = f"Error navigating to subsystem: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            return {"success": False, "error": str(e)}
    
    def upload_active_part(self):
        """
        Загрузка активной детали на сервер
        
        Returns:
            dict: Результат операции
        """
        if not self.main_window:
            return {"success": False, "error": "Главное окно не инициализировано"}
        
        try:
            log("PLMFunctions: Вызов upload_active_part")
            self.main_window.upload_active_part()
            return {
                "success": True,
                "message": "Upload of the active part completed"
            }
        except Exception as e:
            error_msg = f"Error uploading the active part: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            return {"success": False, "error": str(e)} 