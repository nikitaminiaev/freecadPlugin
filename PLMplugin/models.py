class BasicObject:
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.name = data.get('name', 'N/A')
        self.children: list[str] = data.get('children', [])
        self.parents: list[str] = data.get('parents', [])
        # Координаты дочерних объектов из parent_child_module (заполняются сервером для сборок)
        self.children_coordinates: dict = data.get('children_coordinates', {})
        # Полный список записей children с координатами (включая дубликаты)
        # Каждая запись: {"parent_child_module_id": "...", "child_id": "...", "coordinates": {...}}
        self.children_with_coordinates: list[dict] = data.get('children_with_coordinates', [])

        # Поля is_assembly и is_shell теперь находятся внутри bounding_contour
        bounding_contour = data.get('bounding_contour') or {}
        if bounding_contour is None:
             bounding_contour = {}
             
        self.is_assembly = bounding_contour.get('is_assembly', False)
        self.is_shell = bounding_contour.get('is_shell', False)

        # Обработка случая, когда coordinates равно None
        coordinates = data.get('coordinates') or {}
        self.coordinates = {
            "x": coordinates.get('x', 0.0),
            "y": coordinates.get('y', 0.0),
            "z": coordinates.get('z', 0.0),
            "angle": coordinates.get('angle', 0.0),
            "axis": coordinates.get('axis', {}) or {"x": 0.0, "y": 0.0, "z": 0.0}
        }
        
        brep_files = bounding_contour.get('brep_files', {})
        if brep_files is None:
            self.file_path = None
            self.brep_string = None
        else:
            self.file_path = brep_files.get('path')
            self.brep_string = brep_files.get('brep_string')

    @classmethod
    def from_response(cls, response_data):
        if not response_data:
            return None
            
        if isinstance(response_data, list):
            return [cls(obj) for obj in response_data]
        elif isinstance(response_data, dict):
            if 'basic_object' in response_data:
                return cls(response_data['basic_object'])
            elif 'basic_objects' in response_data:
                return [cls(obj) for obj in response_data['basic_objects']]
            else:
                return cls(response_data)
        return None