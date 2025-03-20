"""
Модуль для централизованного логирования в приложении PLM Client.
"""

import time

# Глобальная переменная для управления отладкой
debug = True  # Установите True только для отладки

def log(message):
    """
    Выводит отладочное сообщение, если включен режим отладки.
    
    Args:
        message: Сообщение для логирования
    """
    if debug:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[DEBUG {timestamp}] {message}") 