import asyncio
import json
import os
import logging
from typing import Dict, Set, Optional
from datetime import datetime
from pathlib import Path

# Определяем абсолютный путь к директории программы
PROGRAM_DIR = Path(__file__).parent.absolute()
LOG_FILE = PROGRAM_DIR / 'server.log'

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        # Вывод в консоль
        logging.StreamHandler(),
        # Запись в файл (абсолютный путь)
        logging.FileHandler(str(LOG_FILE), encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class ChatRoom:
    """Класс для управления чат-комнатой и её участниками"""
    
    def __init__(self, name: str):
        # Сохраняем имя комнаты
        self.name = name
        # Множество активных соединений в комнате
        self.members: Set['ClientConnection'] = set()
        # Очередь для асинхронных событий (требование 6)
        self.message_queue = asyncio.Queue()
        logger.info(f"Комната создана: {name}")
    
    async def add_member(self, client: 'ClientConnection'):
        """Добавляем нового участника в комнату"""
        self.members.add(client)
        logger.info(f"{client.username} присоединился к комнате {self.name}")
        # Оповещаем остальных о присоединении нового участника
        message = {
            "type": "system",
            "content": f"{client.username} joined the room",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await self.message_queue.put(message)
    
    async def remove_member(self, client: 'ClientConnection'):
        """Удаляем участника из комнаты"""
        self.members.discard(client)
        logger.info(f"{client.username} покинула комнату {self.name}")
        # Оповещаем остальных об уходе участника
        message = {
            "type": "system",
            "content": f"{client.username} left the room",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await self.message_queue.put(message)
    
    async def post_message(self, client: 'ClientConnection', content: str):
        """Размещаем сообщение в очереди для рассылки"""
        message = {
            "type": "message",
            "sender": client.username,
            "content": content,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        await self.message_queue.put(message)
    
    async def send_private_message(self, from_client: 'ClientConnection', 
                                   to_username: str, content: str) -> bool:
        """Отправляем личное сообщение конкретному участнику"""
        # Ищем участника с указанным именем
        target_member = None
        for member in self.members:
            if member.username == to_username:
                target_member = member
                break
        
        if target_member:
            message = {
                "type": "private",
                "from": from_client.username,
                "content": content,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            # Добавляем в личную очередь получателя
            await target_member.private_queue.put(message)
            logger.info(f"Private message from {from_client.username} to {to_username}")
            return True
        return False


class ClientConnection:
    """Класс для управления подключением отдельного клиента"""
    
    def __init__(self, reader, writer):
        # Читатель для получения данных от клиента
        self.reader = reader
        # Писатель для отправки данных клиенту
        self.writer = writer
        # Имя клиента (устанавливается после аутентификации)
        self.username = None
        # Текущая комната клиента
        self.current_room: Optional[ChatRoom] = None
        # Очередь для личных сообщений (требование 9)
        self.private_queue = asyncio.Queue()
    
    async def send_message(self, data: dict):
        """Отправляем JSON сообщение клиенту"""
        try:
            # Преобразуем данные в JSON
            json_data = json.dumps(data, ensure_ascii=False) + '\n'
            # Отправляем по сокету
            self.writer.write(json_data.encode('utf-8'))
            # Ждем завершения отправки
            await self.writer.drain()
        except Exception as error:
            # Обработка ошибок отправки (требование 7)
            logger.error(f"Ошибка отправки сообщения {self.username}: {error}")
    
    async def receive_message(self) -> Optional[str]:
        """Получаем сообщение от клиента"""
        try:
            # Читаем строку из сокета
            data = await self.reader.readline()
            if not data:
                return None
            return data.decode('utf-8').strip()
        except Exception as error:
            # Обработка ошибок получения (требование 7)
            logger.error(f"Ошибка получения сообщения от {self.username}: {error}")
            return None


class AsyncChatServer:
    """Главный класс асинхронного чат-сервера (требование 1)"""
    
    def __init__(self, host: str = '127.0.0.1', port: int = 8888):
        # Адрес сервера
        self.host = host
        # Порт сервера
        self.port = port
        # Словарь всех комнат {имя_комнаты: объект_комнаты}
        self.rooms: Dict[str, ChatRoom] = {}
        # Множество всех активных клиентов
        self.clients: Set[ClientConnection] = set()
        # Папка для сохранения загруженных файлов (требование 9)
        # Используем абсолютный путь на основе расположения скрипта
        self.uploads_dir = PROGRAM_DIR / "uploaded_files"
        self.uploads_dir.mkdir(exist_ok=True)
        logger.info(f"Сервер инициализирован на {host}:{port}")
        logger.info(f"Директория для загруженных файлов: {self.uploads_dir}")
        logger.info(f"Логи сохраняются в: {LOG_FILE}")
    
    async def handle_client(self, reader, writer):
        """Обрабатываем подключение нового клиента (требование 3)"""
        # Создаем объект соединения для клиента
        client = ClientConnection(reader, writer)
        # Добавляем клиента в множество активных
        self.clients.add(client)
        client_addr = writer.get_extra_info('peername')
        
        try:
            logger.info(f"Новое подключение от {client_addr}")
            
            # Запрашиваем имя пользователя
            await client.send_message({
                "type": "request",
                "message": "Enter your username:"
            })
            
            username = await client.receive_message()
            if not username:
                return
            
            # Сохраняем имя клиента
            client.username = username
            logger.info(f"Клиент подключен: {client.username} ({client_addr})")
            
            # Запрашиваем название комнаты
            await client.send_message({
                "type": "request",
                "message": "Enter room name:"
            })
            
            room_name = await client.receive_message()
            if not room_name:
                return
            
            # Получаем или создаем комнату (требование 4)
            if room_name not in self.rooms:
                # Создаем новую комнату
                self.rooms[room_name] = ChatRoom(room_name)
            
            room = self.rooms[room_name]
            client.current_room = room
            
            # Добавляем клиента в комнату
            await room.add_member(client)
            
            # Отправляем информацию о присоединении
            await client.send_message({
                "type": "success",
                "message": f"Welcome to room '{room_name}'! (Type /help for commands)"
            })
            
            # Создаем две асинхронные задачи для параллельной обработки (требование 3)
            # Задача 1: получение сообщений от клиента
            # Задача 2: отправка сообщений в очередь комнаты и личные сообщения
            tasks = [
                asyncio.create_task(self._receive_from_client(client)),
                asyncio.create_task(self._send_to_client(client))
            ]
            
            # Ждем завершения любой из задач
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            # Если первая задача завершилась, отменяем остальные
            for task in tasks:
                if not task.done():
                    task.cancel()
        
        except asyncio.CancelledError:
            pass
        except Exception as error:
            # Обработка непредвиденных ошибок (требование 7)
            logger.error(f"Ошибка при обработке клиента: {error}")
        finally:
            # Чистка при отключении
            await self._disconnect_client(client)
    
    async def _receive_from_client(self, client: ClientConnection):
        """Получаем и обрабатываем сообщения от клиента"""
        while True:
            # Получаем сообщение от клиента
            message = await client.receive_message()
            
            if not message:
                # Клиент отключился
                break
            
            # Проверяем - это команда или обычное сообщение?
            if message.startswith('/'):
                # Обрабатываем команду
                await self._handle_command(client, message)
            else:
                # Размещаем обычное сообщение в комнате
                if client.current_room:
                    await client.current_room.post_message(client, message)
    
    async def _send_to_client(self, client: ClientConnection):
        """Отправляем сообщения из очереди комнаты и личные сообщения"""
        tasks = []
        
        if client.current_room:
            # Добавляем задачу для получения сообщений из комнаты
            tasks.append(
                asyncio.create_task(
                    self._broadcast_room_messages(client)
                )
            )
        
        # Добавляем задачу для получения личных сообщений
        tasks.append(
            asyncio.create_task(self._send_private_messages(client))
        )
        
        try:
            # Ждем завершения любой из задач
            done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            
            # Если одна завершилась, ждем остальные до конца
            for task in tasks:
                if not task.done():
                    await task
        except asyncio.CancelledError:
            # Отменяем все задачи, если основная задача отменена
            for task in tasks:
                if not task.done():
                    task.cancel()
            raise
    
    async def _broadcast_room_messages(self, client: ClientConnection):
        """Получаем сообщения из очереди комнаты и отправляем клиенту"""
        room = client.current_room
        
        while True:
            try:
                # Получаем сообщение из очереди комнаты (требование 5, 6)
                message = await room.message_queue.get()
                # Отправляем сообщение клиенту
                await client.send_message(message)
            except asyncio.CancelledError:
                break
            except Exception as error:
                logger.error(f"Ошибка при отправке сообщения из комнаты: {error}")
                break
    
    async def _send_private_messages(self, client: ClientConnection):
        """Отправляем личные сообщения клиенту"""
        while True:
            try:
                # Получаем личное сообщение
                message = await client.private_queue.get()
                # Отправляем его клиенту
                await client.send_message(message)
            except asyncio.CancelledError:
                break
            except Exception as error:
                logger.error(f"Ошибка при отправке личного сообщения: {error}")
                break
    
    async def _handle_command(self, client: ClientConnection, command: str):
        """Обрабатываем команды клиента"""
        parts = command.split(maxsplit=1)
        command_type = parts[0].lower()
        
        if command_type == '/help':
            # Показываем доступные команды
            help_text = {
                "type": "system",
                "content": "\n".join([
                    "=== Available Commands ===",
                    "/help - show this help",
                    "/list - show room members",
                    "/private @name message - send private message",
                    "/file - upload file",
                    "/quit - exit chat"
                ])
            }
            await client.send_message(help_text)
        
        elif command_type == '/list':
            # Показываем список участников
            if client.current_room:
                usernames = [
                    member.username 
                    for member in client.current_room.members
                ]
                response = {
                    "type": "system",
                    "content": f"Room members: {', '.join(usernames)}"
                }
                await client.send_message(response)
        
        elif command_type == '/private':
            # Отправляем личное сообщение (требование 9)
            if len(parts) > 1:
                remainder = parts[1]
                # Парсим формат "/private @name message"
                private_parts = remainder.split(maxsplit=1)
                if len(private_parts) >= 2:
                    to_username = private_parts[0].lstrip('@')
                    text = private_parts[1]
                    
                    if client.current_room:
                        success = await client.current_room.send_private_message(
                            client, to_username, text
                        )
                        
                        if success:
                            response = {
                                "type": "system",
                                "content": f"Private message sent to {to_username}"
                            }
                        else:
                            response = {
                                "type": "error",
                                "content": f"User {to_username} not found"
                            }
                        await client.send_message(response)
        
        elif command_type == '/file':
            # Команда для загрузки файла
            file_path = None
            
            # Проверяем, передан ли путь в той же команде (/file /path/to/file)
            if len(parts) > 1:
                # Путь уже в команде
                file_path = parts[1]
                logger.info(f"Путь файла из команды: {file_path}")
            else:
                # Ожидаем путь в следующем сообщении
                await client.send_message({
                    "type": "system",
                    "content": "Send file path to upload"
                })
                
                # Получаем путь файла
                file_path = await client.receive_message()
                if file_path:
                    logger.info(f"Путь файла из сообщения: {file_path}")
            
            if file_path:
                await self._upload_file(client, file_path)
        
        elif command_type == '/quit':
            # Клиент хочет выйти
            raise asyncio.CancelledError()
    
    async def _upload_file(self, client: ClientConnection, file_path: str):
        """Загружаем файл от клиента (требование 9)"""
        try:
            # Очищаем путь от лишних пробелов
            file_path = file_path.strip()
            
            logger.info(f"Получен путь для загрузки: '{file_path}'")
            
            # Преобразуем в Path объект и делаем абсолютным
            file_path_obj = Path(file_path)
            
            # Если относительный путь - делаем его абсолютным
            if not file_path_obj.is_absolute():
                file_path_obj = file_path_obj.absolute()
            
            logger.info(f"Абсолютный путь: {file_path_obj}")
            
            # Проверяем, существует ли файл
            if not file_path_obj.exists():
                error_msg = f"File not found: {file_path_obj}"
                logger.warning(error_msg)
                error = {
                    "type": "error",
                    "content": error_msg
                }
                await client.send_message(error)
                return
            
            # Проверяем, что это файл, а не директория
            if not file_path_obj.is_file():
                error_msg = f"Path is not a file: {file_path_obj}"
                logger.warning(error_msg)
                error = {
                    "type": "error",
                    "content": error_msg
                }
                await client.send_message(error)
                return
            
            # Получаем имя файла
            file_name = file_path_obj.name
            
            # Путь для сохранения
            destination_path = self.uploads_dir / file_name
            
            logger.info(f"Копирование файла из: {file_path_obj}")
            logger.info(f"Сохранение в: {destination_path}")
            
            # Копируем файл
            with open(file_path_obj, 'rb') as source:
                with open(destination_path, 'wb') as dest:
                    content = source.read()
                    dest.write(content)
            
            logger.info(f"Файл успешно загружен: {file_name} ({len(content)} bytes) пользователем {client.username}")
            
            # Сообщаем об успешной загрузке
            success = {
                "type": "system",
                "content": f"File {file_name} uploaded successfully ({len(content)} bytes)"
            }
            await client.send_message(success)
            
            # Оповещаем других участников о загрузке
            if client.current_room:
                message = {
                    "type": "system",
                    "content": f"{client.username} uploaded file: {file_name}"
                }
                await client.current_room.message_queue.put(message)
        
        except Exception as error:
            # Обработка ошибок загрузки (требование 7)
            logger.error(f"Ошибка при загрузке файла: {error}")
            error_response = {
                "type": "error",
                "content": f"File upload error: {str(error)}"
            }
            await client.send_message(error_response)
    
    async def _disconnect_client(self, client: ClientConnection):
        """Отключаем клиента и очищаем ресурсы"""
        # Удаляем клиента из множества активных
        self.clients.discard(client)
        
        # Если клиент был в комнате, удаляем его
        if client.current_room:
            await client.current_room.remove_member(client)
            
            # Если комната пуста, удаляем её
            if len(client.current_room.members) == 0:
                del self.rooms[client.current_room.name]
                logger.info(f"Комната удалена (пуста): {client.current_room.name}")
        
        # Закрываем соединение
        try:
            client.writer.close()
        except:
            pass
        
        logger.info(f"Клиент отключен: {client.username}")
    
    async def start(self):
        """Запускаем сервер и ждем подключений"""
        # Создаем сервер, который слушает на указанном адресе и порту (требование 1)
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port
        )
        
        # Получаем адреса, к которым привязан сервер
        addresses = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        logger.info(f"=== Server started on {addresses} ===")
        
        try:
            # Ждем неопределенное время (сервер работает постоянно)
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as error:
            # Обработка ошибок сервера (требование 7)
            logger.error(f"Server error: {error}")
        finally:
            logger.info("=== Server shutdown ===")


async def main():
    """Главная функция для запуска сервера"""
    # Создаем экземпляр сервера на порту 8888
    chat_server = AsyncChatServer(host='127.0.0.1', port=8888)
    
    # Запускаем сервер
    await chat_server.start()


if __name__ == '__main__':
    # Запускаем асинхронный цикл событий
    asyncio.run(main())
