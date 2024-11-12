class BasicObject:
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.name = data.get('name', 'N/A')
        self.children = data.get('children', [])
        self.parents = data.get('parents', [])

        # Add coordinates field
        coordinates = data.get('coordinates', {})
        self.coordinates = {
            "x": coordinates.get('x', 0.0),
            "y": coordinates.get('y', 0.0),
            "z": coordinates.get('z', 0.0),
            "angle": coordinates.get('angle', 0.0),
            "axis": {
                "x": coordinates.get('axis', {}).get('x', 0.0),
                "y": coordinates.get('axis', {}).get('y', 0.0),
                "z": coordinates.get('axis', {}).get('z', 0.0)
            }
        }
        # Handle case where bounding_contour is None
        bounding_contour = data.get('bounding_contour', {})
        if bounding_contour is None:
            self.file_path = None
            self.brep_string = None
        else:
            brep_files = bounding_contour.get('brep_files', {})
            if brep_files is None:
                self.file_path = None
                self.brep_string = None
            else:
                self.file_path = brep_files.get('path')
                self.brep_string = brep_files.get('brep_string')

    @classmethod
    def from_response(cls, response_data):
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