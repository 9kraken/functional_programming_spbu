"""
Модуль загрузки данных.
Использует функциональный подход для чтения и обработки данных о книгах.
"""

import json
from typing import List, Dict, Any, Iterator
from functools import reduce


def load_books_from_json(filepath: str) -> List[Dict[str, Any]]:
    """
    Загружает книги из JSON файла.
    
    Args:
        filepath: Путь к JSON файлу с книгами
        
    Returns:
        Список словарей с информацией о книгах
        
    Raises:
        FileNotFoundError: Если файл не найден
        json.JSONDecodeError: Если JSON некорректен
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            books = json.load(f)
            return books if isinstance(books, list) else []
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {filepath} не найден")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Ошибка при чтении JSON: {e.msg}", e.doc, e.pos)


def validate_book(book: Dict[str, Any]) -> bool:
    """
    Проверяет, что книга имеет все необходимые поля.
    
    Args:
        book: Словарь с информацией о книге
        
    Returns:
        True если книга валидна, False иначе
    """
    required_fields = {'id', 'title', 'author', 'genre', 'description', 'year', 'keywords'}
    return all(field in book for field in required_fields)


def filter_valid_books(books: List[Dict[str, Any]]) -> Iterator[Dict[str, Any]]:
    """
    Фильтрует список книг, оставляя только валидные.
    Использует генератор для экономии памяти.
    
    Args:
        books: Исходный список книг
        
    Yields:
        Установленные валидные книги
    """
    return (book for book in books if validate_book(book))


def normalize_book(book: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормализует данные книги (приводит к единому виду).
    
    Args:
        book: Исходный словарь книги
        
    Returns:
        Нормализованная книга
    """
    return {
        'id': book.get('id'),
        'title': book.get('title', '').strip(),
        'author': book.get('author', '').strip(),
        'genre': book.get('genre', '').strip().lower(),
        'description': book.get('description', '').strip(),
        'year': int(book.get('year', 0)),
        'keywords': tuple(kw.lower().strip() for kw in book.get('keywords', []))
    }


def load_and_process_books(filepath: str) -> List[Dict[str, Any]]:
    """
    Полная обработка загрузки книг: загрузка -> валидация -> нормализация.
    Композиция функций для обработки данных.
    
    Args:
        filepath: Путь к JSON файлу
        
    Returns:
        Список обработанных книг
    """
    # Загружаем и фильтруем валидные книги
    books = load_books_from_json(filepath)
    valid_books = filter_valid_books(books)
    
    # Нормализуем каждую книгу (map)
    processed_books = list(map(normalize_book, valid_books))
    
    return processed_books


def get_unique_genres(books: List[Dict[str, Any]]) -> List[str]:
    """
    Получает все уникальные жанры из списка книг.
    
    Args:
        books: Список книг
        
    Returns:
        Отсортированный список уникальных жанров
    """
    genres = {book['genre'] for book in books}
    return sorted(genres)


def get_unique_authors(books: List[Dict[str, Any]]) -> List[str]:
    """
    Получает всех уникальных авторов из списка книг.
    
    Args:
        books: Список книг
        
    Returns:
        Отсортированный список уникальных авторов
    """
    authors = {book['author'] for book in books}
    return sorted(authors)


def get_all_keywords(books: List[Dict[str, Any]]) -> List[str]:
    """
    Получает все уникальные ключевые слова из всех книг.
    
    Args:
        books: Список книг
        
    Returns:
        Отсортированный список уникальных ключевых слов
    """
    # Использует reduce для объединения всех ключевых слов
    all_keywords = reduce(
        lambda acc, book: acc | set(book['keywords']),
        books,
        set()
    )
    return sorted(all_keywords)


# Кэширование - можем сохранить обработанные данные
_books_cache = None
_cache_filepath = None


def get_books(filepath: str, use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Получает список книг с опциональным кэшированием.
    
    Args:
        filepath: Путь к файлу
        use_cache: Использовать ли кэш
        
    Returns:
        Список книг
    """
    global _books_cache, _cache_filepath
    
    if use_cache and _books_cache is not None and _cache_filepath == filepath:
        return _books_cache
    
    _books_cache = load_and_process_books(filepath)
    _cache_filepath = filepath
    
    return _books_cache
