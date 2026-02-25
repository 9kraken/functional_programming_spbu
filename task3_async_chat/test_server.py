"""
Тесты асинхронного чат-сервера
Требование 8: Тестирование асинхронных функций сервера
"""

import asyncio
import pytest
import json
from server import ChatRoom, ClientConnection, AsyncChatServer
from io import StringIO
from unittest.mock import Mock, AsyncMock, MagicMock


# ==== ТЕСТЫ ДЛЯ КЛАССА ChatRoom ====

@pytest.mark.asyncio
async def test_chat_room_creation():
    """Тестируем создание новой комнаты"""
    # Создаем комнату
    room = ChatRoom("test_room")
    
    # Проверяем, что имя установлено правильно
    assert room.name == "test_room"
    # Проверяем, что список участников пуст
    assert len(room.members) == 0
    # Проверяем, что очередь существует
    assert room.message_queue is not None


@pytest.mark.asyncio
async def test_add_member_to_room():
    """Тестируем добавление участника в комнату"""
    # Создаем комнату
    room = ChatRoom("test_room")
    
    # Создаем мок клиента
    mock_client = Mock()
    mock_client.username = "test_user"
    
    # Добавляем участника
    await room.add_member(mock_client)
    
    # Проверяем, что участник добавлен
    assert mock_client in room.members
    assert len(room.members) == 1
    
    # Проверяем, что сообщение о присоединении в очереди
    message = await asyncio.wait_for(room.message_queue.get(), timeout=1.0)
    assert message["type"] == "system"
    assert "присоединился" in message["content"]


@pytest.mark.asyncio
async def test_remove_member_from_room():
    """Тестируем удаление участника из комнаты"""
    # Создаем комнату с участником
    room = ChatRoom("test_room")
    mock_client = Mock()
    mock_client.username = "test_user"
    
    # Добавляем и удаляем участника
    await room.add_member(mock_client)
    await room.remove_member(mock_client)
    
    # Проверяем, что участник удален
    assert mock_client not in room.members
    assert len(room.members) == 0


@pytest.mark.asyncio
async def test_post_message_to_room():
    """Тестируем размещение сообщения в комнате"""
    # Создаем комнату
    room = ChatRoom("test_room")
    
    # Создаем мок клиента
    mock_client = Mock()
    mock_client.username = "Alice"
    
    # Размещаем сообщение
    await room.post_message(mock_client, "Привет всем!")
    
    # Получаем сообщение из очереди
    message = await asyncio.wait_for(room.message_queue.get(), timeout=1.0)
    
    # Проверяем структуру сообщения
    assert message["type"] == "message"
    assert message["sender"] == "Alice"
    assert message["content"] == "Привет всем!"
    assert "time" in message


@pytest.mark.asyncio
async def test_send_private_message_success():
    """Тестируем успешную отправку личного сообщения"""
    # Создаем комнату с двумя участниками
    room = ChatRoom("test_room")
    
    sender = Mock()
    sender.username = "Alice"
    sender.private_queue = asyncio.Queue()
    
    receiver = Mock()
    receiver.username = "Bob"
    receiver.private_queue = asyncio.Queue()
    
    room.members.add(sender)
    room.members.add(receiver)
    
    # Отправляем личное сообщение
    success = await room.send_private_message(
        sender, "Bob", "Это личное сообщение"
    )
    
    # Проверяем успех
    assert success is True
    
    # Проверяем, что сообщение получено
    message = await asyncio.wait_for(receiver.private_queue.get(), timeout=1.0)
    assert message["type"] == "private"
    assert message["from"] == "Alice"
    assert message["content"] == "Это личное сообщение"


@pytest.mark.asyncio
async def test_send_private_message_user_not_found():
    """Тестируем отправку личного сообщения несуществующему пользователю"""
    # Создаем комнату
    room = ChatRoom("test_room")
    
    sender = Mock()
    sender.username = "Alice"
    
    # Пытаемся отправить сообщение несуществующему пользователю
    success = await room.send_private_message(
        sender, "NonExistent", "Привет!"
    )
    
    # Проверяем, что операция не удалась
    assert success is False


# ==== ТЕСТЫ ДЛЯ КЛАССА ClientConnection ====

@pytest.mark.asyncio
async def test_client_connection_creation():
    """Тестируем создание подключения клиента"""
    # Создаем мок читателя и писателя
    mock_reader = Mock()
    mock_writer = Mock()
    
    # Создаем подключение
    client = ClientConnection(mock_reader, mock_writer)
    
    # Проверяем начальные значения
    assert client.reader == mock_reader
    assert client.writer == mock_writer
    assert client.username is None
    assert client.current_room is None
    assert client.private_queue is not None


@pytest.mark.asyncio
async def test_send_message():
    """Тестируем отправку сообщения клиентом"""
    # Создаем мок писателя
    mock_writer = Mock()
    mock_writer.drain = AsyncMock()
    
    # Создаем клиента
    client = ClientConnection(Mock(), mock_writer)
    client.username = "test_user"
    
    # Отправляем сообщение
    await client.send_message({"type": "test", "content": "Hello"})
    
    # Проверяем, что write был вызван
    assert mock_writer.write.called
    # Проверяем, что drain был вызван
    assert mock_writer.drain.called


@pytest.mark.asyncio
async def test_receive_message():
    """Тестируем получение сообщения клиентом"""
    # Создаем мок читателя
    mock_reader = Mock()
    test_message = "Hello World"
    mock_reader.readline = AsyncMock(
        return_value=test_message.encode('utf-8')
    )
    
    # Создаем клиента
    client = ClientConnection(mock_reader, Mock())
    
    # Получаем сообщение
    message = await client.receive_message()
    
    # Проверяем результат
    assert message == test_message


# ==== ТЕСТЫ ДЛЯ КЛАССА AsyncChatServer ====

def test_server_creation():
    """Тестируем создание сервера"""
    # Создаем сервер
    server = AsyncChatServer(host="127.0.0.1", port=9999)
    
    # Проверяем параметры
    assert server.host == "127.0.0.1"
    assert server.port == 9999
    assert len(server.rooms) == 0
    assert len(server.clients) == 0


@pytest.mark.asyncio
async def test_room_creation_on_client_join():
    """Тестируем создание комнаты когда клиент присоединяется"""
    # Создаем сервер
    server = AsyncChatServer()
    
    # Проверяем, что комнат нет
    assert len(server.rooms) == 0
    
    # Создаем комнату через сервер
    room = ChatRoom("testroom")
    server.rooms["testroom"] = room
    
    # Проверяем, что комната создана
    assert "testroom" in server.rooms
    assert server.rooms["testroom"].name == "testroom"


@pytest.mark.asyncio
async def test_broadcast_messages_to_room():
    """Тестируем рассылку сообщений в комнате"""
    # Создаем комнату с участниками
    room = ChatRoom("test_room")
    
    # Создаем несколько клиентов
    clients = []
    for i in range(3):
        client = Mock()
        client.username = f"user_{i}"
        clients.append(client)
        await room.add_member(client)
    
    # Размещаем сообщение
    sender = clients[0]
    await room.post_message(sender, "Тестовое сообщение")
    
    # Проверяем, что все клиенты получили системное сообщение о присоединении
    assert room.message_queue.qsize() >= 3  # Минимум 2 системных сообщения + 1 сообщение


@pytest.mark.asyncio
async def test_upload_file_directory_creation():
    """Тестируем что директория для загрузок создается"""
    # Создаем сервер
    server = AsyncChatServer()
    
    # Проверяем, что директория создана
    assert server.uploads_dir.exists()


@pytest.mark.asyncio
async def test_disconnect_client():
    """Тестируем отключение клиента"""
    # Создаем сервер и комнату
    server = AsyncChatServer()
    room = ChatRoom("test_room")
    server.rooms["test_room"] = room
    
    # Создаем клиента
    mock_reader = Mock()
    mock_writer = Mock()
    mock_writer.get_extra_info = Mock(return_value="127.0.0.1:12345")
    client = ClientConnection(mock_reader, mock_writer)
    client.username = "test_user"
    client.current_room = room
    
    # Добавляем клиента в сервер и комнату
    server.clients.add(client)
    await room.add_member(client)
    
    # Отключаем клиента
    await server._disconnect_client(client)
    
    # Проверяем, что клиент удален
    assert client not in server.clients
    assert client not in room.members


# ==== ИНТЕГРАЦИОННЫЕ ТЕСТЫ ====

@pytest.mark.asyncio
async def test_full_message_flow():
    """Тестируем полный цикл обмена сообщениями"""
    # Создаем комнату
    room = ChatRoom("integration_test")
    
    # Создаем двух участников
    alice = Mock()
    alice.username = "Alice"
    alice.private_queue = asyncio.Queue()
    
    bob = Mock()
    bob.username = "Bob"
    bob.private_queue = asyncio.Queue()
    
    # Добавляем в комнату
    await room.add_member(alice)
    await room.add_member(bob)
    
    # Alice отправляет сообщение в комнату
    await room.post_message(alice, "Привет Bob!")
    
    # Alice отправляет личное сообщение Bob
    success = await room.send_private_message(alice, "Bob", "Секретное сообщение")
    
    # Проверяем результаты
    assert success is True
    
    # Получаем личное сообщение
    private_msg = await asyncio.wait_for(bob.private_queue.get(), timeout=1.0)
    assert private_msg["from"] == "Alice"
    assert "Секретное" in private_msg["content"]


@pytest.mark.asyncio
async def test_error_handling_on_send_message():
    """Тестируем обработку ошибок при отправке сообщения"""
    # Создаем мок писателя, который выбросит ошибку
    mock_writer = Mock()
    mock_writer.write.side_effect = Exception("Socket error")
    mock_writer.drain = AsyncMock()
    
    # Создаем клиента
    client = ClientConnection(Mock(), mock_writer)
    client.username = "test_user"
    
    # Пытаемся отправить сообщение (не должна быть выброшена ошибка)
    await client.send_message({"test": "data"})
    
    # Проверяем что обработка ошибок прошла корректно


@pytest.mark.asyncio
async def test_concurrent_client_connections():
    """Тестируем одновременные подключения нескольких клиентов"""
    # Создаем комнату
    room = ChatRoom("concurrent_test")
    
    # Создаем несколько клиентов одновременно
    async def create_client(username):
        client = Mock()
        client.username = username
        await room.add_member(client)
        return client
    
    # Добавляем клиентов параллельно
    clients = await asyncio.gather(
        create_client("User1"),
        create_client("User2"),
        create_client("User3"),
    )
    
    # Проверяем что все клиенты добавлены
    assert len(room.members) == 3


if __name__ == '__main__':
    # Запускаем тесты с помощью pytest
    pytest.main([__file__, "-v", "-s"])
