import socket
import base64
import os
import struct
import random
import time

def create_websocket_client(host, port):
    # Установление TCP-соединения
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)  # Добавляем таймаут
    try:
        print(f"Подключение к {host}:{port}...")
        sock.connect((host, port))
        print("Соединение установлено")
    except ConnectionRefusedError:
        raise Exception(f"Не удалось подключиться к серверу {host}:{port}. Убедитесь, что сервер запущен и порт доступен.")

    # HTTP handshake
    key = base64.b64encode(os.urandom(16)).decode()  # Генерируем случайный ключ
    handshake = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "\r\n"
    )
    sock.sendall(handshake.encode())

    # Проверка ответа сервера
    response = sock.recv(1024).decode('utf-8', errors='replace')
    if "101 Switching Protocols" not in response:
        raise Exception(f"Не удалось установить соединение WebSocket. Ответ сервера: {response}")
    print("WebSocket соединение установлено успешно")

    # Функция отправки сообщения
    def send_message(message):
        if isinstance(message, str):
            message = message.encode('utf-8')
        elif not isinstance(message, bytes):
            message = str(message).encode('utf-8')
            
        # Создаем маску (обязательно для клиентов)
        mask_key = os.urandom(4)
        
        # Маскируем данные
        masked_data = bytearray(message)
        for i in range(len(masked_data)):
            masked_data[i] ^= mask_key[i % 4]
        
        # Определяем длину сообщения
        length = len(message)
        
        # Формируем заголовок
        if length < 126:
            header = struct.pack('!BB', 0x81, 0x80 | length)
        elif length < 65536:
            header = struct.pack('!BBH', 0x81, 0x80 | 126, length)
        else:
            header = struct.pack('!BBQ', 0x81, 0x80 | 127, length)
        
        # Отправляем фрейм: заголовок + маска + маскированные данные
        sock.sendall(header + mask_key + masked_data)

    # Функция получения сообщения
    def receive_message():
        try:
            # Получаем первые 2 байта заголовка
            header = sock.recv(2)
            if not header or len(header) < 2:
                return None
                
            # Разбираем заголовок
            fin = (header[0] & 0x80) != 0
            opcode = header[0] & 0x0F
            has_mask = (header[1] & 0x80) != 0
            length = header[1] & 0x7F
            
            # Получаем расширенную длину, если необходимо
            if length == 126:
                length_bytes = sock.recv(2)
                length = struct.unpack('!H', length_bytes)[0]
            elif length == 127:
                length_bytes = sock.recv(8)
                length = struct.unpack('!Q', length_bytes)[0]
                
            # Получаем маску, если она есть (для сервера)
            mask = None
            if has_mask:
                mask = sock.recv(4)
                
            # Получаем данные
            payload = bytearray()
            remaining = length
            while remaining > 0:
                chunk = sock.recv(min(remaining, 4096))
                if not chunk:
                    break
                payload.extend(chunk)
                remaining -= len(chunk)
                
            # Демаскируем данные, если необходимо
            if has_mask and mask:
                for i in range(len(payload)):
                    payload[i] ^= mask[i % 4]
                    
            # Преобразуем в строку, если это текстовый фрейм
            if opcode == 1:  # Текстовый фрейм
                try:
                    result = payload.decode('utf-8')
                    return result
                except UnicodeDecodeError:
                    return None
            elif opcode == 8:  # Закрытие соединения
                print("Сервер закрыл соединение")
                sock.close()
                return None
            else:
                return payload
        except Exception as e:
            print(f"Ошибка при получении сообщения: {e}")
            return None

    # Функция закрытия соединения
    def close():
        try:
            print("Закрытие WebSocket соединения...")
            # Отправляем фрейм закрытия соединения
            close_frame = struct.pack('!BB', 0x88, 0x80)
            mask_key = os.urandom(4)
            sock.sendall(close_frame + mask_key)
            sock.close()
            print("Соединение закрыто")
        except Exception as e:
            print(f"Ошибка при закрытии соединения: {e}")

    return send_message, receive_message, close

# Пример использования
if __name__ == "__main__":
    # Для Docker контейнера используем IP хост-машины
    host = "0.0.0.0"  # Для локального подключения к контейнеру
    port = 8765
    try:
        send, receive, close = create_websocket_client(host, port)
        
        # Интерактивный режим для отправки сообщений
        print("Введите сообщения для отправки на сервер. Для выхода введите 'exit'")
        
        # Запускаем отдельный поток для прослушивания сообщений от сервера
        def listen_for_messages():
            while True:
                response = receive()
                if response:
                    print(f"Получено от сервера: {response}")
                time.sleep(0.1)  # Небольшая задержка, чтобы не нагружать CPU
        
        import threading
        listener_thread = threading.Thread(target=listen_for_messages)
        listener_thread.daemon = True  # Поток завершится, когда завершится основной поток
        listener_thread.start()
        
        # Основной цикл для отправки сообщений
        while True:
            message = input("> ")
            if message.lower() == 'exit':
                break
            
            send(message)
            
        # Закрываем соединение
        close()
    except Exception as e:
        print(f"Ошибка: {e}")