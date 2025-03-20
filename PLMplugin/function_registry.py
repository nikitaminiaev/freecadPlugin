import json
import traceback
from logger import log

class FunctionRegistry:
    """
    Реестр функций для вызова из внешних JSON-сообщений.
    Позволяет регистрировать функции и вызывать их по имени с аргументами.
    """
    
    def __init__(self):
        # Словарь зарегистрированных функций
        self._functions = {}
        # Функция для отправки результатов через websocket
        self.websocket_sender = None
        
        # Регистрируем стандартные функции
        self._register_default_functions()
    
    def register_function(self, function_name, function_callable):
        """
        Регистрирует функцию в реестре
        
        Args:
            function_name (str): Уникальное имя функции для вызова
            function_callable (callable): Вызываемая функция или метод
        """
        if not callable(function_callable):
            raise ValueError(f"Объект {function_callable} не является вызываемым")
            
        self._functions[function_name] = function_callable
        log(f"Функция {function_name} зарегистрирована в реестре")
    
    def execute_function(self, function_name, function_args=None):
        """
        Выполняет функцию из реестра по имени с указанными аргументами
        
        Args:
            function_name (str): Имя функции для вызова
            function_args (dict): Словарь с аргументами функции (kwargs)
            
        Returns:
            Результат выполнения функции
            
        Raises:
            KeyError: Если функция с указанным именем не зарегистрирована
            Exception: Если возникла ошибка при выполнении функции
        """
        if function_name not in self._functions:
            raise KeyError(f"Функция {function_name} не зарегистрирована в реестре")
            
        log(f"Вызов функции {function_name} с аргументами: {function_args}")
        
        if function_args is None:
            function_args = {}
            
        try:
            # Вызываем функцию с распакованными аргументами
            result = self._functions[function_name](**function_args)
            log(f"Функция {function_name} успешно выполнена, результат: {result}")
            return result
        except Exception as e:
            error_msg = f"Ошибка при выполнении функции {function_name}: {str(e)}\n{traceback.format_exc()}"
            log(error_msg)
            raise
    
    def _register_default_functions(self):
        """Регистрирует стандартные функции, доступные по умолчанию"""
        # Пример регистрации некоторых стандартных функций
        self.register_function("echo", self._echo_function)
        self.register_function("get_available_functions", self._get_available_functions)
        
        # Тут можно добавить другие стандартные функции
        # self.register_function("another_function", self._another_function)
    
    # Примеры стандартных функций
    
    def _echo_function(self, message="Hello World"):
        """Простая тестовая функция, возвращает переданное сообщение"""
        return {"message": message}
    
    def _get_available_functions(self):
        """Возвращает список доступных функций"""
        return {"available_functions": list(self._functions.keys())}
        
    # Добавьте другие стандартные функции здесь
    
    def _send_result_via_websocket(self, function_name, result):
        """Отправляет результат выполнения функции через websocket"""
        if self.websocket_sender:
            try:
                response_data = {
                    "function_response": function_name,
                    "result": result
                }
                self.websocket_sender(response_data)
                return True
            except Exception as e:
                log(f"Ошибка при отправке результата функции через websocket: {str(e)}")
                return False
        return False 