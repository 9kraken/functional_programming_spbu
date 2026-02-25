"""
Демонстрационный скрипт для запуска сервера и нескольких клиентов
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def main():
    """Главная функция демонстрации"""
    print("=" * 60)
    print("Асинхронный чат-сервер - Демонстрация")
    print("=" * 60)
    
    # Получаем текущую директорию
    script_dir = Path(__file__).parent
    
    print("\n📋 Выберите что запустить:")
    print("1. Только сервер")
    print("2. Сервер + текстовый клиент")
    print("3. Сервер + графический клиент")
    print("4. Запустить тесты")
    print("5. Все компоненты (сервер + оба клиента)")
    
    choice = input("\nВведите номер (1-5): ").strip()
    
    if choice == "1":
        # Только сервер
        print("\n🚀 Запускаем сервер...")
        print("Сервер работает на 127.0.0.1:8888")
        print("Нажмите Ctrl+C для остановки\n")
        run_server(script_dir)
    
    elif choice == "2":
        # Сервер + текстовый клиент
        print("\n🚀 Запускаем сервер и текстовый клиент...")
        run_server_and_client(script_dir)
    
    elif choice == "3":
        # Сервер + GUI клиент
        print("\n🚀 Запускаем сервер и графический клиент...")
        run_server_and_gui(script_dir)
    
    elif choice == "4":
        # Тесты
        print("\n🧪 Запускаем тесты...")
        run_tests(script_dir)
    
    elif choice == "5":
        # Все компоненты
        print("\n🚀 Запускаем все компоненты...")
        run_all(script_dir)
    
    else:
        print("❌ Неверный выбор")


def run_server(script_dir):
    """Запускаем только сервер"""
    try:
        subprocess.run(
            [sys.executable, str(script_dir / "server.py")],
            cwd=script_dir
        )
    except KeyboardInterrupt:
        print("\n✓ Сервер остановлен")


def run_server_and_client(script_dir):
    """Запускаем сервер и текстовый клиент"""
    # Запускаем сервер в отдельном процессе
    server_process = subprocess.Popen(
        [sys.executable, str(script_dir / "server.py")],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Ждем запуска сервера
    time.sleep(2)
    
    print("✓ Сервер запущен")
    print("Запускаем клиента...\n")
    
    try:
        # Запускаем клиент
        subprocess.run(
            [sys.executable, str(script_dir / "client.py")],
            cwd=script_dir
        )
    except KeyboardInterrupt:
        print("\n✓ Клиент остановлен")
    finally:
        # Останавливаем сервер
        server_process.terminate()
        print("✓ Сервер остановлен")


def run_server_and_gui(script_dir):
    """Запускаем сервер и GUI клиент"""
    # Запускаем сервер в отдельном процессе
    server_process = subprocess.Popen(
        [sys.executable, str(script_dir / "server.py")],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Ждем запуска сервера
    time.sleep(2)
    
    print("✓ Сервер запущен")
    print("Запускаем GUI клиента...\n")
    
    try:
        # Запускаем GUI клиент
        subprocess.run(
            [sys.executable, str(script_dir / "gui_client.py")],
            cwd=script_dir
        )
    except KeyboardInterrupt:
        print("\n✓ GUI клиент остановлен")
    finally:
        # Останавливаем сервер
        server_process.terminate()
        print("✓ Сервер остановлен")


def run_tests(script_dir):
    """Запускаем тесты"""
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", str(script_dir / "test_server.py"), "-v", "-s"],
            cwd=script_dir
        )
    except Exception as error:
        print(f"❌ Ошибка при запуске тестов: {error}")
        print("\n💡 Убедитесь что установлены зависимости:")
        print("   pip install -r requirements.txt")


def run_all(script_dir):
    """Запускаем все компоненты"""
    print("\n📌 Для полной демонстрации откройте несколько терминалов:\n")
    print("Терминал 1 (сервер):")
    print(f"  python {script_dir / 'server.py'}\n")
    
    print("Терминал 2 (текстовый клиент 1):")
    print(f"  python {script_dir / 'client.py'}\n")
    
    print("Терминал 3 (текстовый клиент 2):")
    print(f"  python {script_dir / 'client.py'}\n")
    
    print("Терминал 4 (GUI клиент):")
    print(f"  python {script_dir / 'gui_client.py'}\n")
    
    print("Терминал 5 (тесты):")
    print(f"  python -m pytest {script_dir / 'test_server.py'} -v\n")
    
    input("Нажмите Enter для запуска сервера...")
    
    # Запускаем сервер в отдельном процессе
    server_process = subprocess.Popen(
        [sys.executable, str(script_dir / "server.py")],
        cwd=script_dir
    )
    
    time.sleep(2)
    print("✓ Сервер запущен on 127.0.0.1:8888")
    print("\nОткройте другие терминалы для запуска клиентов и тестов")
    print("Нажмите Ctrl+C для остановки сервера\n")
    
    try:
        server_process.wait()
    except KeyboardInterrupt:
        print("\n✓ Сервер остановлен")
        server_process.terminate()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✓ Программа завершена")
    except Exception as error:
        print(f"\n❌ Ошибка: {error}")
        sys.exit(1)
