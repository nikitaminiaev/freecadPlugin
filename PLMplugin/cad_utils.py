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
    def save_id(active_doc, id):
        try:
            active_doc.Id = id
            active_doc.save()
        except Exception as e:
            raise Exception(f'File uploaded but failed to save ID to document: {str(e)}')