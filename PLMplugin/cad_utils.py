from dataclasses import dataclass
from typing import Optional, Dict, List, Union

@dataclass
class Coordinates:
    """Coordinates and rotation data for CAD object placement"""
    x: float
    y: float
    z: float
    angle: float
    axis: Dict[str, float]  # Contains x, y, z components of rotation axis


@dataclass
class PartCreationDTO:
    """Data Transfer Object for part creation with BREP data

    Attributes:
        brep_string: String containing BREP data representation of the shape
        id: Optional unique identifier for the part
        label: Optional display label for the part in FreeCAD interface
        coordinates: Optional positioning and rotation data

    Example:
        coords = Coordinates(
            x=0.0, y=0.0, z=0.0,
            angle=0.0,
            axis={'x': 0.0, 'y': 0.0, 'z': 1.0}
        )
        part_data = PartCreationDTO(
            brep_string="... BREP data ...",
            id="unique_id_123",
            label="My Part",
            coordinates=coords
        )
    """
    brep_string: str
    id: Optional[str] = None
    label: Optional[str] = "NewPart"
    coordinates: Optional[Coordinates] = None

    def to_dict(self) -> Dict[str, Union[str, Dict, List]]:
        """Convert DTO to dictionary format for legacy support"""
        result = {
            'brep_string': self.brep_string
        }

        if self.id is not None:
            result['id'] = self.id

        if self.label is not None:
            result['label'] = self.label

        if self.coordinates is not None:
            result['coordinates'] = {
                'x': self.coordinates.x,
                'y': self.coordinates.y,
                'z': self.coordinates.z,
                'angle': self.coordinates.angle,
                'axis': self.coordinates.axis
            }

        return result


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
    def create_part_with_brep(data: PartCreationDTO):
        """Create new Part object with BREP data and properties using DTO

        Args:
            data (PartCreationDTO): Data transfer object containing part creation data
        """
        try:
            import FreeCAD

            doc = FreeCAD.ActiveDocument
            if not doc:
                raise Exception("No active document")

            part_obj = doc.addObject('App::Part', data.label)

            shape = CADUtils.create_shape_from_brep(data.brep_string)
            part_obj.Shape = shape

            CADUtils._set_object_properties(part_obj, data)

            doc.recompute()

            return part_obj
        except Exception as e:
            raise Exception(f'Failed to create part with BREP: {str(e)}')

    @staticmethod
    def _set_object_properties(obj, data: PartCreationDTO) -> None:
        """Set object properties using DTO data

        Args:
            obj: FreeCAD object to set properties for
            data: PartCreationDTO containing property data

        Raises:
            Exception: If setting properties fails
        """
        try:
            if data.id is not None:
                obj.Id = data.id

            if data.coordinates is not None:
                obj.Placement.Base.x = data.coordinates.x
                obj.Placement.Base.y = data.coordinates.y
                obj.Placement.Base.z = data.coordinates.z
                obj.Placement.Rotation.Angle = data.coordinates.angle
                obj.Placement.Rotation.Axis.x = data.coordinates.axis['x']
                obj.Placement.Rotation.Axis.y = data.coordinates.axis['y']
                obj.Placement.Rotation.Axis.z = data.coordinates.axis['z']

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
            import FreeCADGui as Gui
            return Gui.Selection.getSelection()
        except Exception as e:
            raise Exception(f'Failed to select obj: {str(e)}')

    @staticmethod
    def create_dto_from_object(obj) -> PartCreationDTO:
        """Create PartCreationDTO from existing FreeCAD object

        Args:
            obj: FreeCAD object to extract data from

        Returns:
            PartCreationDTO: Data transfer object containing object's properties

        Raises:
            Exception: If data extraction fails
        """
        try:
            # Получаем BREP данные из формы объекта
            brep_string = obj.Shape.exportBrepToString()

            # Создаем объект координат
            coordinates = Coordinates(
                x=obj.Placement.Base.x,
                y=obj.Placement.Base.y,
                z=obj.Placement.Base.z,
                angle=obj.Placement.Rotation.Angle,
                axis={
                    'x': obj.Placement.Rotation.Axis.x,
                    'y': obj.Placement.Rotation.Axis.y,
                    'z': obj.Placement.Rotation.Axis.z
                }
            )

            # Получаем ID объекта, если он есть
            obj_id = getattr(obj, 'Id', None)

            # Создаем DTO
            return PartCreationDTO(
                brep_string=brep_string,
                id=obj_id,
                label=obj.Label,
                coordinates=coordinates
            )

        except Exception as e:
            raise Exception(f'Failed to create DTO from object: {str(e)}')
