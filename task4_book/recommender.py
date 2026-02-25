"""
Модуль рекомендаций.
Использует функциональное программирование (map, filter, reduce) для скорирования и фильтрации книг.
"""

from typing import Dict, List, Callable, Any, Tuple
from functools import reduce
from operator import itemgetter


def score_genre_match(book: Dict, preferred_genres: set) -> float:
    """
    Вычисляет оценку совпадения жанра.
    
    Args:
        book: Информация о книге
        preferred_genres: Множество предпочитаемых жанров
        
    Returns:
        Оценка от 0 до 1
    """
    if not preferred_genres:
        return 0.0
    
    book_genre = book['genre'].lower()
    
    # Если точное совпадение жанра
    if book_genre in preferred_genres:
        return 1.0
    
    # Если частичное совпадение (подстрока)
    for genre in preferred_genres:
        if genre in book_genre or book_genre in genre:
            return 0.7
    
    return 0.0


def score_author_match(book: Dict, preferred_authors: set) -> float:
    """
    Вычисляет оценку совпадения автора.
    
    Args:
        book: Информация о книге
        preferred_authors: Множество предпочитаемых авторов
        
    Returns:
        Оценка от 0 до 1
    """
    if not preferred_authors:
        return 0.0
    
    book_author = book['author'].lower()
    
    # Точное совпадение
    for author in preferred_authors:
        if author == book_author:
            return 1.0
    
    # Частичное совпадение (фамилия)
    for author in preferred_authors:
        if author in book_author or book_author in author:
            return 0.6
    
    return 0.0


def score_keywords_match(book: Dict, preferred_keywords: set) -> float:
    """
    Вычисляет оценку совпадения ключевых слов.
    Использует косинусное сходство.
    
    Args:
        book: Информация о книге
        preferred_keywords: Множество предпочитаемых ключевых слов
        
    Returns:
        Оценка от 0 до 1
    """
    if not preferred_keywords:
        return 0.0
    
    book_keywords = set(book['keywords'])
    
    if not book_keywords:
        return 0.0
    
    # Количество совпадений
    matches = len(book_keywords & preferred_keywords)
    
    # Косинусное сходство: пересечение / объединение
    union = len(book_keywords | preferred_keywords)
    
    if union == 0:
        return 0.0
    
    # Нормализуем к 0-1
    similarity = matches / union
    
    return similarity


def score_year_recency(book: Dict, min_year: int) -> float:
    """
    Вычисляет бонус за новизну книги (если она после min_year).
    
    Args:
        book: Информация о книге
        min_year: Минимальный год
        
    Returns:
        Оценка от 0 до 1
    """
    if min_year <= 0:
        return 1.0
    
    if book['year'] < min_year:
        return 0.0
    
    # Чем ближе год к текущему, тем выше оценка
    # Но это опциональный бонус, не блокирует книгу
    return 1.0


def calculate_matching_score(
    book: Dict,
    preferred_genres: set,
    preferred_authors: set,
    preferred_keywords: set,
    min_year: int = 0,
    genre_weight: float = 0.4,
    author_weight: float = 0.3,
    keywords_weight: float = 0.3
) -> float:
    """
    Вычисляет общий рейтинг соответствия книги предпочтениям.
    Это чистая функция, не имеет побочных эффектов.
    
    Args:
        book: Информация о книге
        preferred_genres: Множество предпочитаемых жанров
        preferred_authors: Множество предпочитаемых авторов
        preferred_keywords: Множество предпочитаемых ключевых слов
        min_year: Минимальный год публикации
        genre_weight: Вес жанра в общей оценке
        author_weight: Вес автора в общей оценке
        keywords_weight: Вес ключевых слов в общей оценке
        
    Returns:
        Итоговая оценка от 0 до 1
    """
    # Вычисляем отдельные оценки
    genre_score = score_genre_match(book, preferred_genres)
    author_score = score_author_match(book, preferred_authors)
    keywords_score = score_keywords_match(book, preferred_keywords)
    year_score = score_year_recency(book, min_year)
    
    # Взвешенная сумма
    weighted_score = (
        genre_score * genre_weight +
        author_score * author_weight +
        keywords_score * keywords_weight
    ) * year_score
    
    return round(weighted_score, 3)


def score_books(
    books: List[Dict],
    preferred_genres: set,
    preferred_authors: set,
    preferred_keywords: set,
    min_year: int = 0
) -> List[Tuple[Dict, float]]:
    """
    Скорирует все книги с использованием map.
    Функция высшего порядка.
    
    Args:
        books: Список книг
        preferred_genres: Множество предпочитаемых жанров
        preferred_authors: Множество предпочитаемых авторов
        preferred_keywords: Множество предпочитаемых ключевых слов
        min_year: Минимальный год публикации
        
    Returns:
        Список кортежей (книга, оценка)
    """
    score_func = lambda book: (
        book,
        calculate_matching_score(
            book, preferred_genres, preferred_authors, preferred_keywords, min_year
        )
    )
    
    return list(map(score_func, books))


def filter_by_score_threshold(
    scored_books: List[Tuple[Dict, float]],
    threshold: float = 0.0
) -> List[Tuple[Dict, float]]:
    """
    Фильтрует книги по минимальной оценке.
    
    Args:
        scored_books: Список кортежей (книга, оценка)
        threshold: Минимальная оценка (0.0-1.0)
        
    Returns:
        Отфильтрованный список
    """
    return list(filter(lambda x: x[1] >= threshold, scored_books))


def filter_by_genre(
    scored_books: List[Tuple[Dict, float]],
    genres: set
) -> List[Tuple[Dict, float]]:
    """
    Фильтрует книги по жанрам.
    
    Args:
        scored_books: Список кортежей (книга, оценка)
        genres: Множество жанров для фильтрации
        
    Returns:
        Отфильтрованный список
    """
    if not genres:
        return scored_books
    
    return list(filter(lambda x: x[0]['genre'].lower() in genres, scored_books))


def filter_by_year(
    scored_books: List[Tuple[Dict, float]],
    min_year: int = 0,
    max_year: int = 9999
) -> List[Tuple[Dict, float]]:
    """
    Фильтрует книги по годам публикации.
    
    Args:
        scored_books: Список кортежей (книга, оценка)
        min_year: Минимальный год
        max_year: Максимальный год
        
    Returns:
        Отфильтрованный список
    """
    return list(filter(
        lambda x: min_year <= x[0]['year'] <= max_year,
        scored_books
    ))


def sort_by_score(scored_books: List[Tuple[Dict, float]]) -> List[Tuple[Dict, float]]:
    """
    Сортирует книги по оценке (убывание).
    
    Args:
        scored_books: Список кортежей (книга, оценка)
        
    Returns:
        Отсортированный список
    """
    return sorted(scored_books, key=itemgetter(1), reverse=True)


def sort_by_title(scored_books: List[Tuple[Dict, float]]) -> List[Tuple[Dict, float]]:
    """
    Сортирует книги по названию (алфавитный порядок).
    
    Args:
        scored_books: Список кортежей (книга, оценка)
        
    Returns:
        Отсортированный список
    """
    return sorted(scored_books, key=lambda x: x[0]['title'])


def sort_by_year(scored_books: List[Tuple[Dict, float]]) -> List[Tuple[Dict, float]]:
    """
    Сортирует книги по году публикации (новые сначала).
    
    Args:
        scored_books: Список кортежей (книга, оценка)
        
    Returns:
        Отсортированный список
    """
    return sorted(scored_books, key=lambda x: x[0]['year'], reverse=True)


def get_recommendations(
    books: List[Dict],
    preferred_genres: set,
    preferred_authors: set,
    preferred_keywords: set,
    min_year: int = 0,
    sort_by: str = 'score',
    filter_genres: set = None,
    threshold: float = 0.0
) -> List[Dict]:
    """
    Главная функция - получить рекомендации.
    Композиция функций: скорирование -> фильтрация -> сортировка.
    
    Args:
        books: Список всех книг
        preferred_genres: Множество предпочитаемых жанров
        preferred_authors: Множество предпочитаемых авторов
        preferred_keywords: Множество предпочитаемых ключевых слов
        min_year: Минимальный год публикации
        sort_by: Способ сортировки ('score', 'title', 'year')
        filter_genres: Жанры для фильтрации (если не None)
        threshold: Минимальная оценка
        
    Returns:
        Список рекомендуемых книг с оценками
    """
    # 1. Скорируем все книги
    scored = score_books(
        books, preferred_genres, preferred_authors, preferred_keywords, min_year
    )
    
    # 2. Фильтруем по минимальной оценке
    scored = filter_by_score_threshold(scored, threshold)
    
    # 3. Фильтруем по жанрам если указано
    if filter_genres:
        scored = filter_by_genre(scored, filter_genres)
    
    # 4. Сортируем
    if sort_by == 'title':
        scored = sort_by_title(scored)
    elif sort_by == 'year':
        scored = sort_by_year(scored)
    else:  # 'score' по умолчанию
        scored = sort_by_score(scored)
    
    # 5. Преобразуем формат: добавляем оценку в словарь книги
    result = []
    for book, score in scored:
        book_with_score = dict(book)
        book_with_score['score'] = score
        result.append(book_with_score)
    
    return result


def get_top_recommendations(
    books: List[Dict],
    preferred_genres: set,
    preferred_authors: set,
    preferred_keywords: set,
    min_year: int = 0,
    limit: int = 5
) -> List[Dict]:
    """
    Получить топ N рекомендаций (удобная функция-обертка).
    
    Args:
        books: Список всех книг
        preferred_genres: Множество предпочитаемых жанров
        preferred_authors: Множество предпочитаемых авторов
        preferred_keywords: Множество предпочитаемых ключевых слов
        min_year: Минимальный год публикации
        limit: Максимальное количество рекомендаций
        
    Returns:
        Список топ-N рекомендаций
    """
    recommendations = get_recommendations(
        books, preferred_genres, preferred_authors, preferred_keywords, min_year
    )
    
    return recommendations[:limit]
