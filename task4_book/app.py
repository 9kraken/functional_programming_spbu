"""
Flask веб-приложение для рекомендательной системы книг.
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from io import StringIO
import csv

from data_loader import get_books, get_unique_genres, get_unique_authors, get_all_keywords
from preferences import normalize_preferences, PreferenceError, preferences_to_sets, get_preference_summary
from recommender import get_recommendations


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

# Получаем путь к файлу с книгами
BOOKS_FILE = os.path.join(os.path.dirname(__file__), 'books.json')

# Загружаем данные один раз при старте
try:
    BOOKS = get_books(BOOKS_FILE)
    GENRES = get_unique_genres(BOOKS)
    AUTHORS = get_unique_authors(BOOKS)
    KEYWORDS = get_all_keywords(BOOKS)
except Exception as e:
    print(f"Ошибка при загрузке данных: {e}")
    BOOKS = []
    GENRES = []
    AUTHORS = []
    KEYWORDS = []


@app.route('/')
def index():
    """Главная страница с формой ввода предпочтений."""
    return render_template('index.html', genres=GENRES, authors=AUTHORS, keywords=KEYWORDS)


@app.route('/api/genres')
def api_genres():
    """API для получения списка жанров."""
    return jsonify(GENRES)


@app.route('/api/authors')
def api_authors():
    """API для получения списка авторов."""
    return jsonify(AUTHORS)


@app.route('/api/keywords')
def api_keywords():
    """API для получения списка ключевых слов."""
    return jsonify(KEYWORDS)


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    """
    API для получения рекомендаций.
    Принимает JSON с предпочтениями пользователя.
    """
    try:
        # Получаем данные из запроса
        data = request.get_json() or request.form.to_dict()
        
        # Нормализуем предпочтения
        preferences = normalize_preferences(data)
        
        # Преобразуем в множества для поиска
        pref_sets = preferences_to_sets(preferences)
        
        # Получаем рекомендации
        sort_by = data.get('sort_by', 'score')
        filter_genres = set(g.lower() for g in data.get('filter_genres', [])) if data.get('filter_genres') else None
        threshold = float(data.get('threshold', 0.0))
        
        recommendations = get_recommendations(
            BOOKS,
            pref_sets['genres'],
            pref_sets['authors'],
            pref_sets['keywords'],
            pref_sets['min_year'],
            sort_by=sort_by,
            filter_genres=filter_genres,
            threshold=threshold
        )
        
        # Преобразуем для JSON (убираем tuple из keywords)
        recommendations = [
            {
                **book,
                'keywords': list(book['keywords']) if isinstance(book['keywords'], tuple) else book['keywords']
            }
            for book in recommendations
        ]
        
        return jsonify({
            'success': True,
            'recommendations': recommendations,
            'count': len(recommendations),
            'preference_summary': get_preference_summary(preferences)
        })
        
    except PreferenceError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Ошибка обработки рекомендаций: {str(e)}"
        }), 500


@app.route('/api/save-recommendations', methods=['POST'])
def api_save_recommendations():
    """
    API для сохранения рекомендаций в CSV файл.
    """
    try:
        data = request.get_json()
        recommendations = data.get('recommendations', [])
        
        if not recommendations:
            return jsonify({
                'success': False,
                'error': 'Нет рекомендаций для сохранения'
            }), 400
        
        # Создаем CSV в памяти
        output = StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=['title', 'author', 'genre', 'year', 'score', 'description']
        )
        
        writer.writeheader()
        for book in recommendations:
            writer.writerow({
                'title': book.get('title', ''),
                'author': book.get('author', ''),
                'genre': book.get('genre', ''),
                'year': book.get('year', ''),
                'score': book.get('score', ''),
                'description': book.get('description', '')
            })
        
        # Возвращаем CSV как attachment
        csv_data = output.getvalue()
        output.close()
        
        filename = f"recommendations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return jsonify({
            'success': True,
            'filename': filename,
            'csv_data': csv_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Ошибка сохранения: {str(e)}"
        }), 500


@app.route('/api/reading-list', methods=['POST'])
def api_reading_list():
    """
    API для управления списком "прочитать".
    Сохраняет в браузер (localStorage), но также может возвращать информацию.
    """
    try:
        data = request.get_json()
        book_id = data.get('book_id')
        action = data.get('action')  # 'add' или 'remove'
        
        return jsonify({
            'success': True,
            'message': f"Книга {action}лена в список прочитать"
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/books/<int:book_id>')
def api_book_detail(book_id):
    """
    API для получения информации об одной книге.
    """
    book = next((b for b in BOOKS if b['id'] == book_id), None)
    
    if not book:
        return jsonify({
            'success': False,
            'error': 'Книга не найдена'
        }), 404
    
    book = dict(book)
    book['keywords'] = list(book['keywords']) if isinstance(book['keywords'], tuple) else book['keywords']
    
    return jsonify({
        'success': True,
        'book': book
    })


@app.route('/api/stats')
def api_stats():
    """
    API для получения статистики по базе данных.
    """
    years = [b['year'] for b in BOOKS]
    
    return jsonify({
        'total_books': len(BOOKS),
        'total_genres': len(GENRES),
        'total_authors': len(AUTHORS),
        'total_keywords': len(KEYWORDS),
        'year_min': min(years) if years else 0,
        'year_max': max(years) if years else 0
    })


@app.errorhandler(404)
def not_found(error):
    """Обработка ошибки 404."""
    return jsonify({
        'success': False,
        'error': 'Страница не найдена'
    }), 404


@app.errorhandler(500)
def server_error(error):
    """Обработка ошибки 500."""
    return jsonify({
        'success': False,
        'error': 'Ошибка сервера'
    }), 500


if __name__ == '__main__':
    # Проверяем, что файл с книгами существует
    if not os.path.exists(BOOKS_FILE):
        print(f"Ошибка: файл {BOOKS_FILE} не найден!")
        exit(1)
    
    if not BOOKS:
        print(f"Ошибка: не удалось загрузить книги из {BOOKS_FILE}")
        exit(1)
    
    print(f"✓ Загружено {len(BOOKS)} книг")
    print(f"✓ {len(GENRES)} жанров")
    print(f"✓ {len(AUTHORS)} авторов")
    
    # Запускаем Flask приложение
    app.run(debug=True, host='127.0.0.1', port=5000)
