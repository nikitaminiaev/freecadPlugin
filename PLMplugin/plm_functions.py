import traceback
from function_registry import FunctionRegistry
from utils.logger import log

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
        function_registry.register_function("save_active_doc", self.save_active_doc)
        
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

    def save_active_doc(self, module_id: str, is_assembly: bool = False, is_shell: bool = False):
        """
        Сохраняет активный документ FreeCAD на сервер (вызывается из веб-интерфейса через WebSocket).

        Режим is_assembly=False (одиночное тело):
            Экспортирует BREP первого найденного тела и обновляет текущий модуль
            через PATCH /api/basic_object/{module_id} с полем brep_files.

        Режим is_assembly=True (сборка из нескольких тел):
            Перебирает все объекты типа App::Part, у которых установлен Id.
            Обновляет координаты дочерних объектов в parent_child_module через
            PATCH /api/basic_object/{module_id} с полем added_children.

        Args:
            module_id (str): ID модуля в базе данных (из URL страницы деталей).
            is_assembly (bool): True — режим сборки (только координаты).
            is_shell (bool): True — тела внутри сборки являются shell-объектами.

        Returns:
            dict: Результат операции.
        """
        if not self.main_window:
            return {"success": False, "error": "Главное окно не инициализировано"}

        try:
            import FreeCAD

            doc = FreeCAD.ActiveDocument
            if not doc:
                return {"success": False, "error": "Нет активного документа FreeCAD"}

            api_client = self.main_window.api_client

            if not is_assembly:
                return self._save_single_body(doc, module_id, is_shell, api_client)

            return self._save_assembly_coordinates(doc, module_id, api_client)

        except ImportError:
            error_msg = "Модуль FreeCAD недоступен"
            log(f"PLMFunctions.save_active_doc: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Ошибка в save_active_doc: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            return {"success": False, "error": str(e)}

    def _save_single_body(self, doc, module_id: str, is_shell: bool, api_client):
        """
        Находит первое тело с Shape в документе, экспортирует BREP и патчит модуль.
        Сохраняет флаг is_shell и сбрасывает is_assembly (одиночная деталь — не сборка).
        """
        brep_string = None
        for obj in doc.Objects:
            if hasattr(obj, 'Shape') and obj.Shape and not obj.Shape.isNull():
                try:
                    brep_string = obj.Shape.exportBrepToString()
                    break
                except Exception:
                    continue

        if not brep_string:
            return {"success": False, "error": "Не найдено ни одного тела с геометрией в активном документе"}

        payload = {
            "brep_files": {"brep_string": brep_string},
            "is_assembly": False,
            "is_shell": is_shell,
        }
        response = api_client.send_patch_request(f"/api/basic_object/{module_id}", payload)

        log(f"PLMFunctions._save_single_body: ответ сервера: {response}")
        return {"success": True, "message": f"BREP сохранён для модуля {module_id}"}

    def _save_assembly_coordinates(self, doc, module_id: str, api_client):
        """
        Перебирает App::Part объекты, собирает их Id и Placement,
        обновляет координаты каждого дочернего объекта через отдельный PATCH-запрос.

        Использует PATCH /api/basic_object/{child_id} с полями parent_id + coordinates,
        что триггерит UPDATE существующей записи в parent_child_module, а не INSERT.
        """
        updated = 0
        errors = []

        for obj in doc.Objects:
            if obj.TypeId != 'App::Part':
                continue

            obj_id = getattr(obj, 'Id', None)
            if not obj_id:
                log(f"PLMFunctions._save_assembly_coordinates: объект {obj.Label} не имеет Id, пропускаем")
                continue

            try:
                axis = obj.Placement.Rotation.Axis
                coordinates = {
                    "x": obj.Placement.Base.x,
                    "y": obj.Placement.Base.y,
                    "z": obj.Placement.Base.z,
                    "angle": obj.Placement.Rotation.Angle,
                    "axis": {"x": axis.x, "y": axis.y, "z": axis.z},
                }
            except Exception as e:
                msg = f"Ошибка чтения Placement для {obj.Label}: {e}"
                log(f"PLMFunctions._save_assembly_coordinates: {msg}")
                errors.append(msg)
                continue

            # PATCH child — обновляет существующую запись в parent_child_module
            payload = {"parent_id": module_id, "coordinates": coordinates}
            response = api_client.send_patch_request(f"/api/basic_object/{obj_id}", payload)
            log(f"PLMFunctions._save_assembly_coordinates: {obj.Label} ({obj_id}) → {response}")
            updated += 1

        if updated == 0:
            return {
                "success": False,
                "error": "Не найдено ни одного App::Part объекта с Id в активном документе",
            }

        result = {"success": True, "message": f"Координаты {updated} дочерних объектов обновлены для модуля {module_id}"}
        if errors:
            result["warnings"] = errors
        return result 