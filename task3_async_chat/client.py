"""
Асинхронный чат-клиент
Requirement 2: Асинхронный клиентский скрипт для подключения к серверу
"""

import asyncio
import json
from typing import Optional


class AsyncChatClient:
    """Асинхронный чат-клиент"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8888):
        # Адрес сервера
        self.host = host
        # Порт сервера
        self.port = port
        # Объект читателя для получения данных
        self.reader = None
        # Объект писателя для отправки данных
        self.writer = None
        # Имя пользователя
        self.username = None
    
    async def connect(self) -> bool:
        """Подключаемся к серверу"""
        try:
            # Устанавливаем подключение к серверу
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            print(f"✓ Connected to server {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            # Сервер не запущен или недоступен
            print(f"✗ Failed to connect to {self.host}:{self.port}")
            return False
        except Exception as error:
            # Обработка других ошибок подключения
            print(f"✗ Connection error: {error}")
            return False
    
    async def send_message(self, message: str):
        """Отправляем сообщение на сервер"""
        try:
            # Кодируем сообщение в UTF-8
            data = message.encode('utf-8') + b'\n'
            # Отправляем по сокету
            self.writer.write(data)
            # Ждем завершения отправки
            await self.writer.drain()
        except Exception as error:
            # Обработка ошибок отправки
            print(f"✗ Send error: {error}")
    
    async def receive_message(self) -> Optional[dict]:
        """Получаем сообщение от сервера"""
        try:
            # Читаем строку из сокета
            data = await self.reader.readline()
            if not data:
                # Соединение закрыто сервером
                return None
            
            # Парсим JSON сообщение
            message = json.loads(data.decode('utf-8'))
            return message
        except json.JSONDecodeError:
            # Неверный JSON формат
            print("✗ Invalid message from server")
            return None
        except Exception as error:
            # Обработка других ошибок
            print(f"✗ Receive error: {error}")
            return None
    
    async def authenticate(self):
        """Аутентифицируем клиента на сервере"""
        # Получаем запрос на имя пользователя
        request = await self.receive_message()
        if request and request.get("type") == "request":
            print(request.get("message", ""))
            
            # Вводим имя пользователя
            username = input("> ").strip()
            if not username:
                username = "AnonymousUser"
            
            # Сохраняем имя пользователя
            self.username = username
            
            # Отправляем имя на сервер
            await self.send_message(username)
        
        # Получаем запрос на название комнаты
        request = await self.receive_message()
        if request and request.get("type") == "request":
            print(request.get("message", ""))
            
            # Вводим название комнаты
            room_name = input("> ").strip()
            if not room_name:
                room_name = "lobby"
            
            # Отправляем название комнаты на сервер
            await self.send_message(room_name)
        
        # Получаем подтверждение подключения
        response = await self.receive_message()
        if response:
            print(f"\n{response.get('message', 'Connected')}\n")
    
    def display_message(self, message: dict):
        """Отображаем полученное сообщение"""
        msg_type = message.get("type", "unknown")
        
        if msg_type == "message":
            # Обычное сообщение из комнаты
            sender = message.get("sender", "Unknown")
            content = message.get("content", "")
            time = message.get("time", "")
            print(f"[{time}] {sender}: {content}")
        
        elif msg_type == "private":
            # Личное сообщение
            sender = message.get("from", "Unknown")
            content = message.get("content", "")
            time = message.get("time", "")
            print(f"[PRIVATE {time}] {sender}: {content}")
        
        elif msg_type == "system":
            # Системное сообщение
            content = message.get("content", "")
            print(f"[SYSTEM] {content}")
        
        elif msg_type == "error":
            # Сообщение об ошибке
            content = message.get("content", "")
            print(f"[ERROR] {content}")
    
    async def input_handler(self):
        """Обрабатываем ввод пользователя в отдельной задаче"""
        loop = asyncio.get_event_loop()
        while True:
            try:
                # Получаем ввод от пользователя в отдельном потоке
                message = await loop.run_in_executor(None, input, ">> ")
                
                if not message:
                    continue
                
                # Отправляем сообщение на сервер
                await self.send_message(message)
            
            except EOFError:
                # Конец ввода
                break
            except Exception as error:
                # Обработка ошибок ввода
                print(f"✗ Error: {error}")
                break
    
    async def message_receiver(self):
        """Получаем сообщения от сервера в отдельной задаче"""
        while True:
            try:
                # Получаем сообщение от сервера
                message = await self.receive_message()
                
                if not message:
                    # Соединение закрыто
                    print("\n✗ Connection closed by server")
                    break
                
                # Отображаем сообщение
                self.display_message(message)
            
            except Exception as error:
                # Обработка ошибок получения
                print(f"✗ Receive error: {error}")
                break
    
    async def run(self):
        """Основной цикл клиента"""
        # Подключаемся к серверу
        if not await self.connect():
            return
        
        try:
            # Аутентифицируем клиента
            await self.authenticate()
            
            # Создаем две асинхронные задачи:
            # Задача 1: получение сообщений от сервера
            # Задача 2: обработка ввода пользователя
            tasks = [
                asyncio.create_task(self.message_receiver()),
                asyncio.create_task(self.input_handler())
            ]
            
            # Ждем завершения любой из задач
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Отменяем оставшиеся задачи
            for task in pending:
                task.cancel()
        
        except KeyboardInterrupt:
            print("\n\n✓ Disconnecting from server...")
        except asyncio.CancelledError:
            pass
        except Exception as error:
            # Обработка непредвиденных ошибок
            print(f"✗ Error: {error}")
        finally:
            # Закрываем соединение
            if self.writer:
                try:
                    self.writer.close()
                except:
                    pass
            
            print("✓ Disconnected from server")


async def main():
    """Главная функция для запуска клиента"""
    # Получаем параметры подключения
    host = input("Server address (127.0.0.1): ").strip() or "127.0.0.1"
    port_str = input("Server port (8888): ").strip() or "8888"
    
    try:
        # Преобразуем строку в число
        port = int(port_str)
    except ValueError:
        print("✗ Invalid port number")
        return
    
    # Создаем объект клиента
    client = AsyncChatClient(host=host, port=port)
    
    # Запускаем клиент
    await client.run()


if __name__ == '__main__':
    # Запускаем асинхронный цикл событий
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✗ Program interrupted by user")
