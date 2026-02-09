from typing import Optional, Union
import base64
from utils.cad_utils import CADUtils
from utils.logger import log


class PartViewCapture:
    """
    Класс для получения скриншотов деталей в различных видах.
    Использует функции CADUtils для работы с FreeCAD.
    """
    
    @staticmethod
    def capture_part_view(part_name: str, view_type: str, 
                         file_path: Optional[str] = None,
                         width: Optional[int] = 800, 
                         height: Optional[int] = 600) -> Union[bytes, str, None]:
        """
        Получает скриншот детали в указанном виде.
        
        Args:
            part_name (str): Название (Label) детали для отображения.
            view_type (str): Тип вида: 'front', 'top', 'right', 'left', 'rear', 'bottom', 'isometric'.
            file_path (Optional[str]): Путь для сохранения файла изображения.
                                      Если None, изображение возвращается как байты.
            width (Optional[int]): Ширина изображения в пикселях.
            height (Optional[int]): Высота изображения в пикселях.
            
        Returns:
            Union[bytes, str, None]: 
                - Если file_path не указан: бинарные данные изображения.
                - Если file_path указан: строка с путем к файлу.
                - None, если произошла ошибка.
                
        Raises:
            Exception: Если деталь не найдена или произошла ошибка при захвате вида.
        """
        try:
            # Находим деталь по названию
            part_obj = CADUtils.get_object_by_label(part_name)
            if not part_obj:
                raise Exception(f"Деталь с названием '{part_name}' не найдена.")
            
            # Устанавливаем указанный вид
            CADUtils.set_standard_view(view_type)
            
            # Захватываем изображение
            image_data = CADUtils.capture_view(file_path, width, height)
            
            # Возвращаем результат
            if file_path:
                return file_path
            else:
                return image_data
                
        except Exception as e:
            log(f"Ошибка при получении скриншота детали '{part_name}': {str(e)}")
            raise
    
    @staticmethod
    def capture_part_view_as_base64(part_name: str, view_type: str,
                                   width: Optional[int] = 800,
                                   height: Optional[int] = 600) -> str:
        """
        Получает скриншот детали в указанном виде и возвращает его в формате base64.
        Удобно для передачи изображения через API или для встраивания в HTML.
        
        Args:
            part_name (str): Название (Label) детали для отображения.
            view_type (str): Тип вида: 'front', 'top', 'right', 'left', 'rear', 'bottom', 'isometric'.
            width (Optional[int]): Ширина изображения в пикселях.
            height (Optional[int]): Высота изображения в пикселях.
            
        Returns:
            str: Строка base64 с данными изображения в формате PNG.
                
        Raises:
            Exception: Если деталь не найдена или произошла ошибка при захвате вида.
        """
        try:
            # Получаем бинарные данные изображения
            image_data = PartViewCapture.capture_part_view(part_name, view_type, 
                                                         None, width, height)
            
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            return base64_data
            
        except Exception as e:
            log(f"Ошибка при получении base64 скриншота детали '{part_name}': {str(e)}")
            raise
