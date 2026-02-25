"""
Модуль для предварительной обработки текстов и анализа данных
"""
import re
from typing import List, Dict, Set, Tuple
from collections import Counter


# Русские стоп-слова (частые слова без смысла)
STOP_WORDS = {
    'это', 'что', 'как', 'их', 'и', 'к', 'в', 'на', 'с', 'по', 'o', 'из',
    'так', 'же', 'или', 'но', 'не', 'вот', 'ведь', 'может', 'всегда',
    'никогда', 'здесь', 'там', 'он', 'она', 'они', 'мы', 'я', 'ты', 'вы',
    'был', 'была', 'было', 'были', 'быть', 'есть', 'был', 'были'
}

# Английские стоп-слова
ENGLISH_STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
    'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
    'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
}


def preprocess_text(text: str) -> List[str]:
    """
    Предварительная обработка текста: нижний регистр, удаление пунктуации, 
    удаление стоп-слов.
    
    Args:
        text: исходный текст
    
    Returns:
        Список слов после обработки
    """
    # Переводим в нижний регистр
    text = text.lower()
    
    # Удаляем ссылки и email
    text = re.sub(r'http\S+|www\S+|[\w.-]+@[\w.-]+\.\w+', '', text)
    
    # Удаляем пунктуацию кроме хэштегов
    text = re.sub(r'[^\w\s#]', ' ', text)
    
    # Разбиваем на слова
    words = text.split()
    
    # Удаляем стоп-слова
    filtered_words = [
        word for word in words
        if word not in STOP_WORDS and word not in ENGLISH_STOP_WORDS
        and len(word) > 2  # Игнорируем очень короткие слова
    ]
    
    return filtered_words


def extract_hashtags(text: str) -> List[str]:
    """
    Извлекает хэштеги из текста.
    
    Args:
        text: текст для анализа
    
    Returns:
        Список найденных хэштегов
    """
    # Используем unicode-aware регулярное выражение для поддержки кириллицы
    return re.findall(r'#[а-яА-Яa-zA-Z0-9_]+', text.lower())


def extract_keywords(words: List[str], top_n: int = 10) -> List[Tuple[str, int]]:
    """
    Извлекает самые популярные ключевые слова.
    
    Args:
        words: список слов
        top_n: количество топ слов
    
    Returns:
        Список (слово, количество) отсортированный по частоте
    """
    counter = Counter(words)
    return counter.most_common(top_n)


def analyze_message(message: Dict) -> Dict:
    """
    Анализирует отдельное сообщение.
    
    Returns:
        Словарь с результатами анализа
    """
    text = message.get('text', '')
    
    # Обработка текста
    words = preprocess_text(text)
    
    # Извлечение хэштегов
    hashtags = extract_hashtags(text)
    
    # Подсчет лайков и шеров
    engagement = message.get('likes', 0) + message.get('shares', 0) * 2
    
    return {
        'original_message': message,
        'processed_words': words,
        'hashtags': hashtags,
        'word_count': len(words),
        'unique_words': len(set(words)),
        'engagement': engagement,
        'source': message.get('source', 'unknown')
    }


def aggregate_analysis(analyzed_messages: List[Dict]) -> Dict:
    """
    Агрегирует анализ всех сообщений для выявления трендов.
    
    Args:
        analyzed_messages: список проанализированных сообщений
    
    Returns:
        Словарь с общей статистикой и трендами
    """
    all_words = []
    all_hashtags = []
    total_engagement = 0
    source_count = {}
    source_engagement = {}  # Ангажированность по источникам
    top_sources = Counter()
    
    print(f"[DEBUG] Начало агрегирования {len(analyzed_messages)} сообщений")
    
    for idx, analysis in enumerate(analyzed_messages):
        words = analysis.get('processed_words', [])
        hashtags = analysis.get('hashtags', [])
        engagement = analysis.get('engagement', 0)
        source = analysis.get('source', 'unknown')
        
        all_words.extend(words)
        all_hashtags.extend(hashtags)
        total_engagement += engagement
        
        source_count[source] = source_count.get(source, 0) + 1
        source_engagement[source] = source_engagement.get(source, 0) + engagement
        top_sources[source] += engagement
        
        if (idx + 1) % 50 == 0:
            print(f"[DEBUG] Обработано {idx + 1}/{len(analyzed_messages)} сообщений")
            print(f"[DEBUG]   - Найдено слов: {len(all_words)}")
            print(f"[DEBUG]   - Найдено хэштегов: {len(all_hashtags)}")
    
    print(f"[DEBUG] Всего обработано:")
    print(f"[DEBUG]   - Сообщений: {len(analyzed_messages)}")
    print(f"[DEBUG]   - Уникальных слов: {len(set(all_words))}")
    print(f"[DEBUG]   - Уникальных хэштегов: {len(set(all_hashtags))}")
    print(f"[DEBUG]   - Всего ангажирования: {total_engagement}")
    print(f"[DEBUG]   - Источники: {dict(source_count)}")
    
    # Получаем топ ключевые слова
    top_keywords = extract_keywords(all_words, top_n=20)
    print(f"[DEBUG] Топ ключевые слова: {top_keywords[:5]}")
    
    # Получаем топ хэштеги
    hashtag_counter = Counter(all_hashtags)
    top_hashtags = hashtag_counter.most_common(15)
    print(f"[DEBUG] Топ хэштеги: {top_hashtags[:5] if top_hashtags else 'НЕ НАЙДЕНЫ'}")
    
    # Получаем топ источники по ангажированности
    top_engaged_sources = top_sources.most_common(5)
    
    result = {
        'total_messages': len(analyzed_messages),
        'total_words_processed': len(all_words),
        'unique_words': len(set(all_words)),
        'total_hashtags': len(all_hashtags),
        'unique_hashtags': len(set(all_hashtags)),
        'total_engagement': total_engagement,
        'average_engagement_per_message': (
            total_engagement / max(len(analyzed_messages), 1)
        ),
        'top_keywords': top_keywords,
        'top_hashtags': top_hashtags,
        'source_distribution': source_count,
        'source_engagement': source_engagement,
        'top_sources_by_engagement': top_engaged_sources,
        'trending_topics': [word for word, _ in top_keywords[:10]] if top_keywords else []
    }
    
    print(f"[DEBUG] Финальный результат: {len(result)} полей")
    return result
