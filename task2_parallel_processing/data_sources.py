"""
Модуль для генерации данных из различных источников социальных сетей
"""
import random
from typing import List, Dict
from datetime import datetime, timedelta


# Примеры текстов из разных социальных сетей
SAMPLE_TEXTS = {
    "VK": [
        "Удивительный новый фильм про киберпанк! #кино #фантастика #будущее",
        "Сегодня ходили на концерт, было отлично! #музыка #развлечение",
        "Python это самый крутой язык программирования #python #программирование",
        "Искусственный интеллект меняет мир #ИИ #технология #будущее",
        "Новые результаты исследований показывают интересные тренды #наука",
        "Всем привет! Как вы относитесь к роботизации? #робот #автоматизация",
        "Космос всегда манил человечество #космос #исследования #вселенная"
    ],
    "Telegram": [
        "Breaking news: новые открытия в науке! #новости #наука #исследование",
        "Рекомендую прочитать эту статью про машинное обучение #ML #ИИ",
        "Обновление: новая версия приложения уже доступна #app #update",
        "Интересное видео про квантовые компьютеры #video #quantum #computing",
        "Следите за нашим каналом для свежих новостей #news #update"
    ],
    "Facebook": [
        "Happy to announce our new project! #project #excited #happy",
        "Поздравляю всех с началом нового года! #2024 #celebration #newyear",
        "Семейная поездка была просто чудесной #family #travel #amazing",
        "Спасибо за поддержку! #gratitude #thanks #community",
        "Делюсь моим хобби: веб-дизайн #webdesign #creative #hobby"
    ],
    "Instagram": [
        "Красивый закат сегодня! #sunset #photography #beautiful #nature",
        "Мой новый проект: фотография #photo #art #creative",
        "Путешествие в горы было невероятным! #mountains #travel #adventure",
        "Мой питомец такой милый #pet #cute #animals #love",
        "Новый look в этом сезоне #fashion #style #trendy"
    ],
    "Twitter": [
        "Новый тренд в tecnología: blockchain #blockchain #crypto #tech",
        "Должны быть изменения в регуляции #politics #regulation #important",
        "Спорт объединяет людей! #sports #unity #passion",
        "Климатические изменения требуют действий #climate #action #future",
        "Инновации в здравоохранении спасают жизни #healthcare #innovation"
    ],
    "Reddit": [
        "AMA: я разработчик игр, спрашивайте меня о чём угодно! #gaming #developer",
        "Лучшие советы по программированию #programming #code #tips",
        "Обсуждение: должны ли роботы иметь права? #AI #ethics #discussion",
        "Поделитесь своим успехом в обучении Python #python #learning #success",
        "Проблема с багами в продакшене как ее решить #debugging #coding"
    ],
    "LinkedIn": [
        "Рад объявить о новой должности! #jobchange #newchallenge #grateful",
        "Советы по карьере в tech индустрии #career #tech #advice",
        "Важность сетевых контактов #networking #business #connections",
        "Тренды в цифровой трансформации #digitaltransformation #business",
        "Обучение и развитие ключ к успеху #learning #development #growth"
    ],
    "TikTok": [
        "Забавный танец на новый трек! #dance #fun #trending #viral",
        "Лайфхак как сделать кофе идеально #lifehack #coffee #tips",
        "Мой день в роли программиста #coding #dayinmylife #developer",
        "Смешной момент с моим котом #funny #cat #cute #pets",
        "Новинка в мире фитнеса и спорта #fitness #sports #trending"
    ],
    "YouTube": [
        "Смотрите наш новый видео о машинном обучении! #ML #tutorial #learning",
        "Обзор последних гаджетов 2024 #review #gadgets #tech #unboxing",
        "Как стать успешным в IT индустрии #IT #career #motivation",
        "Топ 10 лучших фильмов года #movies #review #cinema #entertainment",
        "Путеводитель по странам: Япония #travel #japan #vlog #adventure"
    ],
    "Pinterest": [
        "Идеи для интерьера дома #homedesign #interior #DIY #furniture",
        "Лучшие рецепты здорового питания #recipes #healthy #cooking #food",
        "Идеи для свадебного оформления #wedding #decoration #ideas #planning",
        "Модные тренды сезона весна-лето #fashion #trends #style #lookbook",
        "Растения для уютного дома #plants #gardening #homeandgarden #greenery"
    ]
}

SOURCES = list(SAMPLE_TEXTS.keys())


def fetch_from_source(source_name: str, message_count: int = 50) -> List[Dict[str, str]]:
    """
    Имитирует получение данных из конкретного источника.
    
    Args:
        source_name: название источника (VK, Telegram, Facebook и т.д.)
        message_count: количество сообщений для генерации
    
    Returns:
        Список сообщений из источника
    """
    messages = []
    source_texts = SAMPLE_TEXTS.get(source_name, [])
    
    if not source_texts:
        return messages
    
    for i in range(message_count):
        message = {
            "source": source_name,
            "id": f"{source_name}_{i}",
            "text": random.choice(source_texts),
            "timestamp": (
                datetime.now() - timedelta(hours=random.randint(1, 72))
            ).isoformat(),
            "likes": random.randint(0, 10000),
            "shares": random.randint(0, 1000),
            "comments": random.randint(0, 500)
        }
        messages.append(message)
    
    return messages


def get_all_sources() -> List[str]:
    """Получить список всех доступных источников"""
    return SOURCES
