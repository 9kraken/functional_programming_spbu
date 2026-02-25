"""
Графическая оболочка асинхронного чат-клиента
Требование 10: Полноценная графическая оболочка для клиента
"""

import asyncio
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from typing import Optional
import threading


class ConnectDialog(tk.Toplevel):
    """Диалоговое окно подключения"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Подключение к серверу")
        self.geometry("400x250")
        self.resizable(False, False)
        # Делаем окно модальным
        self.transient(parent)
        self.grab_set()
        
        # Результат
        self.result = None
        
        # Результат для проверки
        self.ready = False
        
        self._create_widgets()
        # Центрируем окно на главном окне
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (400 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (250 // 2)
        self.geometry(f"+{x}+{y}")
    
    def _create_widgets(self):
        """Создаем элементы диалога"""
        # Рамка для полей
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Адрес сервера
        tk.Label(frame, text="Адрес сервера:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.host_entry = tk.Entry(frame, font=("Arial", 10), width=30)
        self.host_entry.insert(0, "127.0.0.1")
        self.host_entry.grid(row=0, column=1, sticky="ew", pady=5)
        
        # Порт сервера
        tk.Label(frame, text="Порт сервера:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        self.port_entry = tk.Entry(frame, font=("Arial", 10), width=30)
        self.port_entry.insert(0, "8888")
        self.port_entry.grid(row=1, column=1, sticky="ew", pady=5)
        
        # Имя пользователя
        tk.Label(frame, text="Ваше имя:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        self.username_entry = tk.Entry(frame, font=("Arial", 10), width=30)
        self.username_entry.grid(row=2, column=1, sticky="ew", pady=5)
        
        # Комната
        tk.Label(frame, text="Название комнаты:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        self.room_entry = tk.Entry(frame, font=("Arial", 10), width=30)
        self.room_entry.insert(0, "lobby")
        self.room_entry.grid(row=3, column=1, sticky="ew", pady=5)
        
        # Кнопки
        button_frame = tk.Frame(frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        tk.Button(button_frame, text="Подключиться", command=self.ok_click,
                  bg="green", fg="white", font=("Arial", 10, "bold"), width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Отмена", command=self.cancel_click,
                  bg="red", fg="white", font=("Arial", 10, "bold"), width=12).pack(side=tk.LEFT, padx=5)
        
        # Фокус на первое поле
        self.host_entry.focus()
    
    def ok_click(self):
        """Обработчик нажатия ОК"""
        host = self.host_entry.get().strip()
        port_str = self.port_entry.get().strip()
        username = self.username_entry.get().strip()
        room = self.room_entry.get().strip()
        
        # Валидация
        if not host:
            messagebox.showerror("Error", "Enter server address")
            return
        
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
            return
        
        if not username:
            messagebox.showerror("Error", "Enter your name")
            return
        
        if not room:
            room = "lobby"
        
        # Сохраняем результат
        self.result = {
            "host": host,
            "port": port,
            "username": username,
            "room": room
        }
        self.destroy()
    
    def cancel_click(self):
        """Обработчик отмены"""
        self.result = None
        self.destroy()


class AsyncChatGUI:
    """Класс графической оболочки чат-клиента"""
    
    def __init__(self, root):
        # Главное окно
        self.root = root
        self.root.title("Async Chat Client")
        self.root.geometry("700x750")
        
        # Соединение с сервером
        self.reader = None
        self.writer = None
        # Имя пользователя
        self.username = None
        # Имя комнаты
        self.room_name = None
        # Флаг подключения
        self.is_connected = False
        # Асинхронный цикл событий
        self.loop = None
        
        # Создаем интерфейс
        self._create_widgets()
        
        # Запускаем асинхронный цикл в отдельном потоке
        self.start_event_loop()
    
    def _create_widgets(self):
        """Создаем элементы интерфейса"""
        # ==== Верхняя панель с информацией ====
        info_frame = tk.Frame(self.root, bg="lightblue", height=60)
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Информация о подключении
        self.status_label = tk.Label(
            info_frame, text="Статус: Не подключено", bg="lightblue", font=("Arial", 10, "bold")
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Информация о пользователе и комнате
        self.user_info_label = tk.Label(
            info_frame, text="", bg="lightblue", font=("Arial", 9)
        )
        self.user_info_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # ==== Кнопки управления ====
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        # Кнопка подключения
        self.connect_button = tk.Button(
            button_frame, text="Подключиться", command=self.on_connect_click,
            bg="green", fg="white", font=("Arial", 10, "bold"), width=12
        )
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка отключения
        self.disconnect_button = tk.Button(
            button_frame, text="Отключиться", command=self.on_disconnect_click,
            bg="red", fg="white", font=("Arial", 10, "bold"), width=12, state=tk.DISABLED
        )
        self.disconnect_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка загрузки файла
        self.upload_button = tk.Button(
            button_frame, text="Загрузить файл", command=self.on_upload_click,
            bg="orange", fg="white", font=("Arial", 10, "bold"), width=12, state=tk.DISABLED
        )
        self.upload_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка справки
        help_button = tk.Button(
            button_frame, text="Справка", command=self.show_help,
            bg="blue", fg="white", font=("Arial", 10, "bold"), width=12
        )
        help_button.pack(side=tk.LEFT, padx=5)
        
        # ==== Область сообщений ====
        messages_label = tk.Label(
            self.root, text="Сообщения:", font=("Arial", 10, "bold")
        )
        messages_label.pack(side=tk.TOP, anchor="w", padx=5, pady=(5, 0))
        
        # Текстовая область для сообщений (только для чтения)
        self.messages_text = scrolledtext.ScrolledText(
            self.root, height=20, width=85, state=tk.DISABLED,
            font=("Courier", 10), bg="white", fg="black"
        )
        self.messages_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Конфигурируем стили для разных типов сообщений
        self.messages_text.tag_config("system", foreground="blue", font=("Courier", 10, "bold"))
        self.messages_text.tag_config("private", foreground="purple", font=("Courier", 10, "bold"))
        self.messages_text.tag_config("error", foreground="red", font=("Courier", 10, "bold"))
        self.messages_text.tag_config("regular", foreground="black")
        
        # ==== Нижняя панель с вводом ====
        input_label = tk.Label(
            self.root, text="Сообщение:", font=("Arial", 10, "bold")
        )
        input_label.pack(side=tk.TOP, anchor="w", padx=5, pady=(5, 0))
        
        # Поле для ввода сообщения
        self.input_entry = tk.Entry(
            self.root, font=("Arial", 10), state=tk.DISABLED
        )
        self.input_entry.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        self.input_entry.bind("<Return>", self.on_send_message)
        
        # Кнопка отправки
        self.send_button = tk.Button(
            self.root, text="Отправить", command=self.send_message,
            bg="lightgreen", fg="black", font=("Arial", 10, "bold"), state=tk.DISABLED
        )
        self.send_button.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
    
    def start_event_loop(self):
        """Запускаем асинхронный цикл событий в отдельном потоке"""
        def run_loop():
            # Создаем новый цикл событий для потока
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            # Запускаем цикл
            self.loop.run_forever()
        
        # Запускаем цикл в фоновом потоке
        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()
    
    def on_connect_click(self):
        """Обработчик клика на кнопку подключения"""
        # Создаем диалог подключения
        dialog = ConnectDialog(self.root)
        self.root.wait_window(dialog)
        
        # Если диалог был отменен
        if dialog.result is None:
            return
        
        # Получаем результаты
        host = dialog.result["host"]
        port = dialog.result["port"]
        username = dialog.result["username"]
        room_name = dialog.result["room"]
        
        # Сохраняем параметры
        self.username = username
        self.room_name = room_name
        
        # Запускаем подключение в асинхронном цикле
        asyncio.run_coroutine_threadsafe(
            self._connect_to_server(host, port),
            self.loop
        )
    
    async def _connect_to_server(self, host: str, port: int):
        """Подключаемся к серверу асинхронно"""
        try:
            # Устанавливаем подключение
            self.reader, self.writer = await asyncio.open_connection(host, port)
            self.is_connected = True
            
            # Обновляем интерфейс в главном потоке
            self.root.after(0, self._update_connected_state)
            
            # Получаем запрос на имя и отправляем его
            message = await self._receive_message()
            if message and message.get("type") == "request":
                await self._send_message_str(self.username)
            
            # Получаем запрос на комнату и отправляем её
            message = await self._receive_message()
            if message and message.get("type") == "request":
                await self._send_message_str(self.room_name)
            
            # Получаем сообщение приветствия
            message = await self._receive_message()
            if message:
                self.root.after(
                    0,
                    self._display_message,
                    {"type": "system", "content": message.get("message", "Connected")}
                )
            
            # Запускаем получение сообщений
            await self._receive_messages_loop()
        
        except Exception as error:
            # Показываем ошибку
            self.root.after(
                0,
                messagebox.showerror,
                "Ошибка подключения",
                f"Не удалось подключиться: {error}"
            )
            self.is_connected = False
            self.root.after(0, self._update_disconnected_state)
    
    async def _receive_message(self) -> Optional[dict]:
        """Получаем одно сообщение от сервера"""
        try:
            # Читаем данные из сокета
            data = await self.reader.readline()
            if not data:
                return None
            
            # Парсим JSON
            message = json.loads(data.decode('utf-8'))
            return message
        except json.JSONDecodeError:
            return None
        except Exception as error:
            print(f"Receive error: {error}")
            return None
    
    async def _send_message_str(self, message: str):
        """Отправляем строку на сервер"""
        try:
            # Кодируем в UTF-8 и отправляем
            data = (message + '\n').encode('utf-8')
            self.writer.write(data)
            await self.writer.drain()
        except Exception as error:
            print(f"Send error: {error}")
    
    async def _receive_messages_loop(self):
        """Цикл получения сообщений от сервера"""
        while self.is_connected:
            try:
                # Получаем сообщение
                message = await self._receive_message()
                
                if not message:
                    # Соединение закрыто
                    break
                
                # Отображаем сообщение в главном потоке
                self.root.after(0, self._display_message, message)
            
            except Exception as error:
                logger.error(f"Receive loop error: {error}")
                break
        
        # Отключаемся
        self.is_connected = False
        self.root.after(0, self._update_disconnected_state)
        logger.info(f"Client {self.username} disconnected")
    
    def _display_message(self, message: dict):
        """Отображаем сообщение в текстовой области"""
        msg_type = message.get("type", "regular")
        
        # Формируем текст сообщения
        if msg_type == "message":
            # Обычное сообщение
            sender = message.get("sender", "Unknown")
            content = message.get("content", "")
            time = message.get("time", "")
            text = f"[{time}] {sender}: {content}\n"
            tag = "regular"
        
        elif msg_type == "private":
            # Личное сообщение
            sender = message.get("from", "Unknown")
            content = message.get("content", "")
            time = message.get("time", "")
            text = f"[PRIVATE {time}] {sender}: {content}\n"
            tag = "private"
        
        elif msg_type == "system":
            # Системное сообщение
            content = message.get("content", "")
            text = f"[SYSTEM] {content}\n"
            tag = "system"
        
        elif msg_type == "error":
            # Сообщение об ошибке
            content = message.get("content", "")
            text = f"[ERROR] {content}\n"
            tag = "error"
        
        else:
            # Неизвестный тип
            text = f"{message}\n"
            tag = "regular"
        
        # Добавляем текст в область сообщений
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.insert(tk.END, text, tag)
        self.messages_text.see(tk.END)  # Прокручиваем к концу
        self.messages_text.config(state=tk.DISABLED)
    
    def send_message(self):
        """Отправляем сообщение на сервер"""
        # Получаем текст из поля ввода
        message = self.input_entry.get().strip()
        
        if not message:
            return
        
        # Отправляем в асинхронном цикле
        asyncio.run_coroutine_threadsafe(
            self._send_message_str(message),
            self.loop
        )
        
        # Очищаем поле ввода
        self.input_entry.delete(0, tk.END)
    
    def on_send_message(self, event):
        """Обработчик клавиши Enter в поле ввода"""
        self.send_message()
    
    def on_upload_click(self):
        """Обработчик клика на кнопку загрузки файла"""
        # Открываем диалог выбора файла
        file_path = filedialog.askopenfilename(
            title="Выберите файл для загрузки",
            initialdir=".",
            filetypes=[("Все файлы", "*.*")]
        )
        
        if file_path:
            # Отправляем команду загрузки
            command = f"/file {file_path}"
            asyncio.run_coroutine_threadsafe(
                self._send_message_str(command),
                self.loop
            )
    
    def on_disconnect_click(self):
        """Обработчик клика на кнопку отключения"""
        # Отключаемся
        self.is_connected = False
        
        if self.writer:
            try:
                self.writer.close()
            except:
                pass
        
        # Обновляем интерфейс
        self._update_disconnected_state()
        self._display_message({"type": "system", "content": "Отключено от сервера"})
    
    def _update_connected_state(self):
        """Обновляем интерфейс после подключения"""
        # Обновляем статус
        self.status_label.config(text="Статус: ✓ Подключено")
        self.user_info_label.config(text=f"{self.username} | Комната: {self.room_name}")
        
        # Активируем элементы
        self.connect_button.config(state=tk.DISABLED)
        self.disconnect_button.config(state=tk.NORMAL)
        self.upload_button.config(state=tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        self.send_button.config(state=tk.NORMAL)
    
    def _update_disconnected_state(self):
        """Обновляем интерфейс после отключения"""
        # Обновляем статус
        self.status_label.config(text="Статус: ✗ Не подключено")
        self.user_info_label.config(text="")
        
        # Деактивируем элементы
        self.connect_button.config(state=tk.NORMAL)
        self.disconnect_button.config(state=tk.DISABLED)
        self.upload_button.config(state=tk.DISABLED)
        self.input_entry.config(state=tk.DISABLED)
        self.send_button.config(state=tk.DISABLED)
    
    def show_help(self):
        """Показываем справку"""
        help_text = """
=== Справка по использованию чата ===

Команды:
  /help - показать эту справку
  /list - показать участников комнаты
  /private @name сообщение - отправить личное сообщение
  /file - загрузить файл
  /quit - выход из чата

Советы:
  • Введите сообщение и нажмите Enter или кнопку "Отправить"
  • Личные сообщения помечены как [PRIVATE]
  • Системные сообщения помечены как [SYSTEM]
  • Ошибки показаны красным [ERROR]
  • Используйте кнопку "Загрузить файл" для выбора файла
        """
        messagebox.showinfo("Справка", help_text)


def main():
    """Главная функция для запуска графической оболочки"""
    # Создаем главное окно
    root = tk.Tk()
    
    # Создаем приложение
    app = AsyncChatGUI(root)
    
    # Запускаем главное окно
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Программа прервана пользователем")


if __name__ == '__main__':
    main()
