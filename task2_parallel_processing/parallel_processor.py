"""
Главный модуль для параллельной обработки данных из социальных сетей
Использует multiprocessing для параллельной обработки и анализа данных
"""
import json
import time
import os
from multiprocessing import Pool, Manager
from typing import List, Dict
from datetime import datetime

from data_sources import fetch_from_source, get_all_sources
from text_analysis import analyze_message, aggregate_analysis

# Определяем директорию, где находится этот модуль
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


def process_source_data(source_name: str) -> tuple:
    """
    Обрабатывает данные из одного источника.
    Выполняется в отдельном процессе.
    
    Args:
        source_name: название источника
    
    Returns:
        Кортеж (название источника, список проанализированных сообщений)
    """
    print(f"[PROCESS-{source_name}] Начало обработки источника")
    
    # Получаем данные из источника
    messages = fetch_from_source(source_name, message_count=50)
    print(f"[PROCESS-{source_name}] Загружено {len(messages)} сообщений")
    
    # Анализируем каждое сообщение
    analyzed = [analyze_message(msg) for msg in messages]
    print(f"[PROCESS-{source_name}] Анализировано {len(analyzed)} сообщений")
    
    # Статистика по этому источнику
    total_words = sum(len(a.get('processed_words', [])) for a in analyzed)
    total_hashtags = sum(len(a.get('hashtags', [])) for a in analyzed)
    total_engagement = sum(a.get('engagement', 0) for a in analyzed)
    
    print(f"[PROCESS-{source_name}] Статистика:")
    print(f"[PROCESS-{source_name}]   - Всего слов обработано: {total_words}")
    print(f"[PROCESS-{source_name}]   - Хэштегов найдено: {total_hashtags}")
    print(f"[PROCESS-{source_name}]   - Ангажирования: {total_engagement}")
    print(f"[PROCESS-{source_name}] ✓ Завершена обработка")
    
    return source_name, analyzed


def run_parallel_processing(num_workers: int = 4) -> Dict:
    """
    Главная функция для параллельной обработки данных.
    
    Args:
        num_workers: количество рабочих процессов
    
    Returns:
        Словарь с результатами анализа
    """
    start_time = time.time()
    
    print(f"\n{'='*70}")
    print("ПАРАЛЛЕЛЬНАЯ ОБРАБОТКА ДАННЫХ ИЗ СОЦИАЛЬНЫХ СЕТЕЙ")
    print(f"{'='*70}\n")
    
    sources = get_all_sources()
    print(f"[INFO] Найденные источники: {', '.join(sources)}")
    print(f"[INFO] Количество рабочих процессов: {num_workers}\n")
    
    # Используем multiprocessing Pool для параллельной обработки
    all_analyzed_messages = []
    source_results = {}
    
    print("[PHASE 1] Параллельная загрузка данных из {0} источников...".format(len(sources)))
    phase1_start = time.time()
    
    with Pool(processes=num_workers) as pool:
        results = pool.map(process_source_data, sources)
    
    phase1_time = time.time() - phase1_start
    
    # Собираем результаты
    print("\n[PHASE 1] Обработка результатов...")
    for source_name, analyzed in results:
        source_results[source_name] = {
            'message_count': len(analyzed),
            'messages': analyzed
        }
        all_analyzed_messages.extend(analyzed)
        print(f"[PHASE 1] ✓ {source_name}: {len(analyzed)} сообщений добавлено")
    
    print(f"\n[SUCCESS] Фаза 1 завершена за {phase1_time:.2f} сек")
    print(f"[INFO] Всего загружено сообщений: {len(all_analyzed_messages)}")
    print(f"[INFO] Источников обработано: {len(source_results)}\n")
    
    # Фаза 2: Анализ данных
    print("[PHASE 2] Анализ и выявление трендов...")
    phase2_start = time.time()
    
    analysis_results = aggregate_analysis(all_analyzed_messages)
    
    phase2_time = time.time() - phase2_start
    print(f"[SUCCESS] Фаза 2 завершена за {phase2_time:.2f} сек\n")
    
    # Общее время выполнения
    total_time = time.time() - start_time
    
    # Формируем финальный отчет
    report = {
        'timestamp': datetime.now().isoformat(),
        'execution_summary': {
            'total_execution_time': f"{total_time:.2f} сек",
            'phase1_time': f"{phase1_time:.2f} сек (загрузка данных)",
            'phase2_time': f"{phase2_time:.2f} сек (анализ)",
            'num_workers': num_workers,
            'total_messages_processed': len(all_analyzed_messages)
        },
        'source_statistics': {
            source_name: source_results[source_name]['message_count']
            for source_name in source_results
        },
        'analysis_results': analysis_results
    }
    
    return report


def print_report(report: Dict) -> None:
    """
    Красиво выводит отчет в консоль.
    
    Args:
        report: словарь с результатами анализа
    """
    print(f"\n{'='*70}")
    print("РЕЗУЛЬТАТЫ АНАЛИЗА")
    print(f"{'='*70}\n")
    
    # Сводка выполнения
    summary = report.get('execution_summary', {})
    print("[ВРЕМЯ ВЫПОЛНЕНИЯ]")
    print(f"  Общее время: {summary.get('total_execution_time', 'N/A')}")
    print(f"  Фаза 1 (загрузка): {summary.get('phase1_time', 'N/A')}")
    print(f"  Фаза 2 (анализ): {summary.get('phase2_time', 'N/A')}")
    print(f"  Рабочих процессов: {summary.get('num_workers', 'N/A')}\n")
    
    # Статистика источников
    sources = report.get('source_statistics', {})
    print("[СТАТИСТИКА ИСТОЧНИКОВ]")
    total_by_source = sum(sources.values())
    for source, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        percent = (count / total_by_source * 100) if total_by_source > 0 else 0
        print(f"  {source:12} : {count:3} сообщений ({percent:5.1f}%)")
    print()
    
    # Результаты анализа
    analysis = report.get('analysis_results', {})
    
    print("[ОБЩАЯ СТАТИСТИКА]")
    print(f"  Всего сообщений: {analysis.get('total_messages', 0)}")
    print(f"  Всего слов обработано: {analysis.get('total_words_processed', 0)}")
    print(f"  Уникальных слов: {analysis.get('unique_words', 0)}")
    print(f"  Всего хэштегов: {analysis.get('total_hashtags', 0)}")
    print(f"  Уникальных хэштегов: {analysis.get('unique_hashtags', 0)}")
    print(f"  Всего ангажированности: {analysis.get('total_engagement', 0)}")
    print(f"  Средняя ангажированность: {analysis.get('average_engagement_per_message', 0):.2f}\n")
    
    # Топ ключевые слова
    keywords = analysis.get('top_keywords', [])
    if keywords:
        print("[ТОП 20 КЛЮЧЕВЫХ СЛОВ]")
        for i, (word, count) in enumerate(keywords[:20], 1):
            print(f"  {i:2}. {word:20} : {count:4} раз")
        print()
    
    # Топ хэштеги
    hashtags = analysis.get('top_hashtags', [])
    if hashtags:
        print("[ТОП 15 ХЭШТЕГОВ]")
        for i, (tag, count) in enumerate(hashtags[:15], 1):
            print(f"  {i:2}. {tag:20} : {count:4} раз")
        print()
    
    # Топ источники по ангажированности
    top_sources = analysis.get('top_sources_by_engagement', [])
    if top_sources:
        print("[ТОП ИСТОЧНИКИ ПО АНГАЖИРОВАННОСТИ]")
        for i, (source, engagement) in enumerate(top_sources, 1):
            print(f"  {i}. {source:15} : {engagement:7} ангажированности")
        print()
    
    # Выявленные тренды
    topics = analysis.get('trending_topics', [])
    if topics:
        print("[ВЫЯВЛЕННЫЕ ТРЕНДЫ]")
        for i, topic in enumerate(topics[:15], 1):
            print(f"  {i:2}. {topic}")
        print()


def save_report(report: Dict, filename: str = "analysis_results.json") -> None:
    """
    Сохраняет отчет в JSON файл.
    
    Args:
        report: словарь с результатами
        filename: название файла для сохранения
    """
    # Создаем абсолютный путь в папке модуля
    filepath = os.path.join(MODULE_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] Отчет сохранен в {filepath}")
