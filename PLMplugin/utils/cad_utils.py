from dataclasses import dataclass
from typing import Any, Optional, Dict, List, Union
import os
import tempfile
from utils.logger import log

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

VIEW_COMMANDS = {
    "front": "Std_ViewFront",        # Вид спереди
    "top": "Std_ViewTop",          # Вид сверху
    "right": "Std_ViewRight",        # Вид справа
    "left": "Std_ViewLeft",         # Вид слева
    "rear": "Std_ViewRear",         # Вид сзади
    "bottom": "Std_ViewBottom",      # Вид снизу
    "isometric": "Std_ViewIsometric" # Альтернативное имя для изометрии
}

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
    def close_active_doc():
        try:
            import FreeCAD
            FreeCAD.closeDocument(FreeCAD.ActiveDocument.Name)
        except Exception as e:
            pass

    @staticmethod
    def set_id(active_doc, id):
        try:
            active_doc.Id = id
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
            import FreeCADGui as Gui
            doc = FreeCAD.ActiveDocument
            if not doc:
                raise Exception("No active document")

            part_obj = doc.addObject('App::Part', data.label)
            body_obj = doc.addObject('Part::Feature', 'Body')

            shape = CADUtils._create_shape_from_brep(data.brep_string)
            body_obj.Shape = shape
            part_obj.Group = [body_obj]
            CADUtils._set_object_properties(part_obj, data)

            return part_obj
        except Exception as e:
            raise Exception(f'Failed to create part with BREP: {str(e)}')
    
    @staticmethod
    def recompute_doc():
        try:
            import FreeCAD
            import FreeCADGui as Gui
            doc = FreeCAD.ActiveDocument
            doc.recompute()
            Gui.SendMsgToActiveView("ViewFit")
        except Exception as e:
            raise Exception(f'Failed to recompute document: {str(e)}')

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
    def _create_shape_from_brep(brep_string):
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

    @staticmethod
    def get_combined_brep_from_objects(objects=None):
        """Объединяет несколько объектов в один BREP

        Args:
            objects: Список объектов FreeCAD. Если None, берутся выбранные объекты.

        Returns:
            str: BREP строка объединенной формы

        Raises:
            Exception: Если не удалось объединить объекты или получить BREP
        """
        try:
            if objects is None:
                objects = CADUtils.get_all_selected_obj()
            
            if not objects:
                raise Exception("Не выбрано ни одного объекта")
                
            # Получаем формы всех объектов
            shapes = [obj.Shape for obj in objects]
            
            # Объединяем все формы в одну
            combined_shape = shapes[0].fuse(shapes[1:])
            
            # Экспортируем в BREP
            return combined_shape.exportBrepToString()
            
        except Exception as e:
            raise Exception(f'Не удалось получить объединенный BREP: {str(e)}')

    @staticmethod
    def get_object_by_label(label: str) -> Optional[Any]:
        """Находит первый объект в активном документе по его свойству Label.

        Args:
            label (str): Имя (Label) объекта для поиска.

        Returns:
            Optional[Any]: Найденный объект FreeCAD или None, если объект с таким Label не найден.

        Raises:
            Exception: Если нет активного документа.
        """
        try:
            import FreeCAD
            doc = FreeCAD.ActiveDocument
            if not doc:
                # Можно просто вернуть None или вывести предупреждение,
                # но выброс исключения более явно сообщает о проблеме.
                raise Exception("Нет активного документа для поиска объекта.")

            # Перебираем все объекты в документе
            for obj in doc.Objects:
                # Проверяем, есть ли у объекта свойство Label и совпадает ли оно
                if hasattr(obj, 'Label') and obj.Label == label:
                    return obj # Возвращаем первый найденный объект

            # Если цикл завершился, а объект не найден
            return None

        except Exception as e:
            return None

    @staticmethod
    def set_standard_view(view_type: str):
        """Устанавливает стандартный вид (спереди, сверху, изометрия и т.д.).

        Args:
            view_type (str): Тип вида. Допустимые значения (регистронезависимые):
                             'front', 'top', 'right', 'left', 'rear', 'bottom', 'iso'/'isometric'.
        """
        try:
            import FreeCADGui as Gui
            if not Gui.ActiveDocument or not hasattr(Gui.ActiveDocument, 'ActiveView'):
                raise Exception("Active document or view not found.")

            command = VIEW_COMMANDS.get(view_type.lower())

            if command:
                Gui.runCommand(command, 0) # Выполняем команду установки вида
            else:
                valid_views = ", ".join(VIEW_COMMANDS.keys())
                raise ValueError(f"Unknown view type: '{view_type}'. Available standard views: {valid_views}")

        except Exception as e:
            raise Exception(f"Failed to set standard view: {str(e)}")
        
    @staticmethod
    def capture_view(file_path: Optional[str] = None, width: Optional[int] = None, height: Optional[int] = None) -> Optional[bytes]:
        """Захватывает текущий активный вид в виде изображения.

        Args:
            file_path (Optional[str]): Путь для сохранения файла изображения.
                                       Если None, изображение возвращается как байты.
                                       Формат файла определяется расширением (e.g., .png, .jpg).
            width (Optional[int]): Ширина изображения в пикселях. Если None, используется текущая ширина вида.
            height (Optional[int]): Высота изображения в пикселях. Если None, используется текущая высота вида.

        Returns:
            Optional[bytes]: Бинарные данные изображения (в формате PNG), если file_path равен None.
                             None, если изображение было сохранено в файл.

        Raises:
            Exception: Если не удалось получить активный вид или сохранить/прочитать изображение.
        """
        try:
            import FreeCADGui as Gui
            
            # Проверяем, есть ли активный документ и вид в GUI
            if not Gui.ActiveDocument or not hasattr(Gui.ActiveDocument, 'ActiveView'):
                 raise Exception("Активный документ или вид не найден.")

            view = Gui.ActiveDocument.ActiveView

            # Определяем размеры: если не заданы, используем текущие размеры вида
            # Обратите внимание: получение текущих размеров может быть не всегда надежно,
            # лучше явно указывать размеры, если это возможно.
            # Здесь мы передаем None в saveImage, если размеры не указаны,
            # позволяя FreeCAD использовать свои значения по умолчанию или текущие.

            if file_path:
                # Вариант 1: Сохранение в файл
                print(f"Сохранение вида в файл: {file_path}")
                view.saveImage(file_path, width, height)
                print(f"Вид успешно сохранен в {file_path}")
                return None
            else:
                # Вариант 2: Возврат данных изображения как байтов
                temp_path = None
                try:
                    # Создаем временный файл с расширением .png
                    fd, temp_path = tempfile.mkstemp(suffix=".png")
                    os.close(fd) # Закрываем дескриптор, так как saveImage работает с путем

                    log(f"Saving view to temporary file: {temp_path}")
                    # Сохраняем во временный файл
                    view.saveImage(temp_path, width, height)

                    log(f"Reading data from temporary file: {temp_path}")
                    # Читаем бинарные данные из временного файла
                    with open(temp_path, 'rb') as f:
                        image_data = f.read()
                    
                    log(f"Temporary file read, data size: {len(image_data)} bytes")
                    return image_data

                finally:
                    # Гарантированно удаляем временный файл
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                            log(f"Temporary file removed: {temp_path}")
                        except OSError as e:
                            log(f"Failed to remove temporary file {temp_path}: {e}")

        except Exception as e:
            # Логируем или перевыбрасываем исключение
            log(f"Error capturing view: {str(e)}")
            raise Exception(f"Error capturing view: {str(e)}") 