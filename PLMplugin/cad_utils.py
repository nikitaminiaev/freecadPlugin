class CADUtils:
    @staticmethod
    def open_file(file_path: str):
        try:
            import FreeCAD
            FreeCAD.open(file_path)
        except Exception as e:
            raise Exception(f"Failed to open file in FreeCAD: {str(e)}")