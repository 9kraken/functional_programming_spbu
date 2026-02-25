"""
Модуль обработки пользовательских предпочтений.
Использует функциональный подход для парсинга и обработки ввода.
"""

from typing import Dict, List, Set, Tuple
from functools import reduce


class PreferenceError(Exception):
    """Исключение для ошибок в предпочтениях."""
    pass


def parse_comma_separated(text: str) -> List[str]:
    """
    Парсит текст, разделенный запятыми.
    
    Args:
        text: Входная строка
        
    Returns:
        Список очищенных элементов
    """
    if not text or not isinstance(text, str):
        return []
    
    # Разделяем по запятым, очищаем, фильтруем пустые
    items = map(str.strip, text.split(','))
    items = filter(lambda x: x, items)  # Убираем пустые строки
    items = map(str.lower, items)  # Приводим к нижнему регистру
    
    return list(items)


def validate_preferences(preferences: Dict) -> bool:
    """
    Проверяет, что предпочтения заполнены правильно.
    
    Args:
        preferences: Словарь предпочтений
        
    Returns:
        True если валидны
        
    Raises:
        PreferenceError: Если предпочтения невалидны
    """
    if not preferences:
        raise PreferenceError("Предпочтения не могут быть пустыми")
    
    # Проверяем, что есть хотя бы одно заполненное поле
    has_content = any([
        preferences.get('genres'),
        preferences.get('authors'),
        preferences.get('keywords')
    ])
    
    if not has_content:
        raise PreferenceError("Заполните хотя бы одно поле: жанры, авторы или ключевые слова")
    
    return True


def normalize_preferences(raw_preferences: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Нормализует сырые предпочтения пользователя.
    
    Args:
        raw_preferences: Сырой словарь предпочтений от формы
        
    Returns:
        Нормализованный словарь
        
    Raises:
        PreferenceError: Если ошибка в предпочтениях
    """
    normalized = {
        'genres': parse_comma_separated(raw_preferences.get('genres', '')),
        'authors': parse_comma_separated(raw_preferences.get('authors', '')),
        'keywords': parse_comma_separated(raw_preferences.get('keywords', '')),
        'min_year': int(raw_preferences.get('min_year', 0)) if raw_preferences.get('min_year') else 0
    }
    
    # Проверяем валидность
    validate_preferences(normalized)
    
    return normalized


def create_preference_dict(
    genres: List[str] = None,
    authors: List[str] = None,
    keywords: List[str] = None,
    min_year: int = 0
) -> Dict:
    """
    Создает словарь предпочтений.
    
    Args:
        genres: Список предпочитаемых жанров
        authors: Список предпочитаемых авторов
        keywords: Список предпочитаемых ключевых слов
        min_year: Минимальный год публикации
        
    Returns:
        Словарь предпочтений
    """
    return {
        'genres': genres or [],
        'authors': authors or [],
        'keywords': keywords or [],
        'min_year': max(0, min_year)
    }


def preferences_to_sets(preferences: Dict) -> Dict[str, Set]:
    """
    Преобразует предпочтения в множества для быстрого поиска.
    
    Args:
        preferences: Словарь предпочтений
        
    Returns:
        Словарь с множествами
    """
    return {
        'genres': set(map(str.lower, preferences.get('genres', []))),
        'authors': set(map(str.lower, preferences.get('authors', []))),
        'keywords': set(map(str.lower, preferences.get('keywords', []))),
        'min_year': preferences.get('min_year', 0)
    }


def get_preference_summary(preferences: Dict) -> str:
    """
    Возвращает текстовое описание предпочтений.
    
    Args:
        preferences: Словарь предпочтений
        
    Returns:
        Строка с описанием предпочтений
    """
    parts = []
    
    if preferences.get('genres'):
        parts.append(f"Жанры: {', '.join(preferences['genres'])}")
    
    if preferences.get('authors'):
        parts.append(f"Авторы: {', '.join(preferences['authors'])}")
    
    if preferences.get('keywords'):
        parts.append(f"Ключевые слова: {', '.join(preferences['keywords'])}")
    
    if preferences.get('min_year', 0) > 0:
        parts.append(f"После {preferences['min_year']} года")
    
    return "; ".join(parts) if parts else "Нет выбранных предпочтений"


def merge_preferences(*preference_dicts) -> Dict:
    """
    Объединяет несколько словарей предпочтений (функция высшего порядка).
    
    Args:
        *preference_dicts: Несколько словарей предпочтений
        
    Returns:
        Объединенный словарь
    """
    def merge_two(pref1: Dict, pref2: Dict) -> Dict:
        """Объединяет два словаря предпочтений."""
        return {
            'genres': list(set(pref1.get('genres', []) + pref2.get('genres', []))),
            'authors': list(set(pref1.get('authors', []) + pref2.get('authors', []))),
            'keywords': list(set(pref1.get('keywords', []) + pref2.get('keywords', []))),
            'min_year': max(pref1.get('min_year', 0), pref2.get('min_year', 0))
        }
    
    if not preference_dicts:
        return create_preference_dict()
    
    return reduce(merge_two, preference_dicts)
