class CADUtils:
    @staticmethod
    def open_file(file_path: str):
        try:
            import FreeCAD
            FreeCAD.open(file_path)
        except Exception as e:
            raise Exception(f"Failed to open file in FreeCAD: {str(e)}")

    @staticmethod
    def get_active_doc():
        try:
            import FreeCAD
            active_doc = FreeCAD.ActiveDocument
            if not active_doc:
                raise Exception('Warning', 'No active document found in FreeCAD!')
            return active_doc
        except Exception as e:
            raise Exception(f"Failed to open file in FreeCAD: {str(e)}")

    @staticmethod
    def create_new_doc(name: str):
        try:
            import FreeCAD
            active_doc = FreeCAD.newDocument(name)
            return active_doc
        except Exception as e:
            raise Exception(f"Failed to create new file in FreeCAD: {str(e)}")

    @staticmethod
    def save_id(active_doc, id):
        try:
            active_doc.Id = id
            active_doc.save()
        except Exception as e:
            raise Exception(f'File uploaded but failed to save ID to document: {str(e)}')

    @staticmethod
    def create_part_with_brep(data):
        """Create new Part object with BREP data and properties

        Args:
            data (dict): Dictionary containing:
                - brep_string: BREP data string
                - id (optional): Object Id
                - label (optional): Object Label
                - coordinates (optional): [x, y, z] coordinates
        """
        try:
            import FreeCAD

            doc = FreeCAD.ActiveDocument
            if not doc:
                raise Exception("No active document")

            if 'brep_string' not in data:
                raise Exception("BREP data not provided in data dictionary")

            label = data.get('label', 'NewPart')

            part_obj = doc.addObject('App::Part', label)

            shape = CADUtils.create_shape_from_brep(data['brep_string'])
            part_obj.Shape = shape

            CADUtils._set_object_properties(part_obj, data)

            doc.recompute()

            return part_obj
        except Exception as e:
            raise Exception(f'Failed to create part with BREP: {str(e)}')

    @staticmethod
    def _set_object_properties(obj, data):
        try:
            if 'id' in data:
                obj.Id = data['id']

            if 'coordinates' in data:
                coords = data['coordinates']
                if isinstance(coords, (list, tuple)) and len(coords) == 3:
                    obj.Placement.Base.x = coords['x']
                    obj.Placement.Base.y = coords['y']
                    obj.Placement.Base.z = coords['z']
                    obj.Placement.Rotation.Angle = coords['angle']
                    obj.Placement.Rotation.Axis.x = coords['axis']['x']
                    obj.Placement.Rotation.Axis.y = coords['axis']['y']
                    obj.Placement.Rotation.Axis.z = coords['axis']['z']

        except Exception as e:
            raise Exception(f'Failed to set object properties: {str(e)}')

    @staticmethod
    def set_object_group(obj, group_objects):
        """Set the Group property of an object with a list of child objects

        Args:
            obj: The parent object to set the Group property for
            group_objects (list): List of objects to be added as children
        """
        try:
            if not isinstance(group_objects, (list, tuple)):
                raise Exception("Group objects must be provided as a list or tuple")
            obj.Group = group_objects
        except Exception as e:
            raise Exception(f'Failed to set object group: {str(e)}')

    @staticmethod
    def create_shape_from_brep(brep_string):
        """Create shape object from BREP string"""
        try:
            import Part
            shape = Part.Shape()
            shape.importBrepFromString(brep_string)
            return shape
        except Exception as e:
            raise Exception(f'Failed to create shape from BREP: {str(e)}')


    @staticmethod
    def get_all_selected_obj():
        try:
            return Gui.Selection.getSelection()
        except Exception as e:
            raise Exception(f'Failed to select obj: {str(e)}')
