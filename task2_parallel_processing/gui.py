"""
GUI для параллельной обработки данных из социальных сетей
Использует tkinter для графического интерфейса
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import threading
import time
import os
from datetime import datetime
from typing import Dict

from parallel_processor import run_parallel_processing

# Определяем директорию, где находится этот модуль
MODULE_DIR = os.path.dirname(os.path.abspath(__file__))


class ParallelProcessorGUI:
    """Графический интерфейс для параллельной обработки"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Анализ данных социальных сетей")
        self.root.geometry("1200x800")
        
        self.is_running = False
        self.analysis_results = None
        
        # Стили
        self.root.style = ttk.Style()
        self.root.style.theme_use('clam')
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создает все виджеты интерфейса"""
        
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # ========== ВЕРХНЯЯ ПАНЕЛЬ ==========
        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Кнопка запуска
        self.start_button = ttk.Button(
            control_frame,
            text="▶ Запустить анализ",
            command=self._start_analysis,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка остановки
        self.stop_button = ttk.Button(
            control_frame,
            text="⏹ Остановить",
            command=self._stop_analysis,
            state=tk.DISABLED,
            width=20
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Кнопка сохранения
        self.save_button = ttk.Button(
            control_frame,
            text="💾 Сохранить результаты",
            command=self._save_results,
            state=tk.DISABLED,
            width=20
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Спиннер для рабочих процессов
        ttk.Label(control_frame, text="Рабочих процессов:").pack(side=tk.LEFT, padx=(20, 5))
        self.workers_var = tk.IntVar(value=4)
        workers_spin = ttk.Spinbox(
            control_frame,
            from_=1,
            to=8,
            textvariable=self.workers_var,
            width=5,
            state='readonly'
        )
        workers_spin.pack(side=tk.LEFT, padx=5)
        
        # ========== СТАТУС И ПРОГРЕСС ==========
        status_frame = ttk.LabelFrame(main_frame, text="Статус", padding="10")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Статусная строка
        self.status_label = ttk.Label(status_frame, text="Готово к запуску")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(
            status_frame,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(side=tk.LEFT, padx=20, fill=tk.X, expand=True)
        
        # ========== НОУТБУК (ТАБЫ) ==========
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Таб 1: Лог обработки
        self._create_log_tab()
        
        # Таб 2: Ключевые слова
        self._create_keywords_tab()
        
        # Таб 3: Хэштеги
        self._create_hashtags_tab()
        
        # Таб 4: Тренды
        self._create_trends_tab()
        
        # Таб 5: Статистика
        self._create_stats_tab()
        
        # Конфигурация расширения
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def _create_log_tab(self):
        """Таб с логом обработки"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="📋 Лог обработки")
        
        # Текстовое поле с логом
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=20,
            width=100,
            wrap=tk.WORD,
            bg="#f0f0f0"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
    
    def _create_keywords_tab(self):
        """Таб с ключевыми словами"""
        keywords_frame = ttk.Frame(self.notebook)
        self.notebook.add(keywords_frame, text="🔑 Ключевые слова")
        
        # Таблица для ключевых слов
        columns = ("Место", "Слово", "Количество")
        self.keywords_tree = ttk.Treeview(
            keywords_frame,
            columns=columns,
            height=25,
            show='tree headings'
        )
        
        self.keywords_tree.column("#0", width=0, stretch=tk.NO)
        self.keywords_tree.column("Место", anchor=tk.CENTER, width=60)
        self.keywords_tree.column("Слово", anchor=tk.W, width=300)
        self.keywords_tree.column("Количество", anchor=tk.CENTER, width=100)
        
        self.keywords_tree.heading("Место", text="Место")
        self.keywords_tree.heading("Слово", text="Ключевое слово")
        self.keywords_tree.heading("Количество", text="Количество")
        
        scrollbar = ttk.Scrollbar(keywords_frame, orient=tk.VERTICAL, command=self.keywords_tree.yview)
        self.keywords_tree.configure(yscroll=scrollbar.set)
        
        self.keywords_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_hashtags_tab(self):
        """Таб с хэштегами"""
        hashtags_frame = ttk.Frame(self.notebook)
        self.notebook.add(hashtags_frame, text="# Хэштеги")
        
        columns = ("Место", "Хэштег", "Количество")
        self.hashtags_tree = ttk.Treeview(
            hashtags_frame,
            columns=columns,
            height=25,
            show='tree headings'
        )
        
        self.hashtags_tree.column("#0", width=0, stretch=tk.NO)
        self.hashtags_tree.column("Место", anchor=tk.CENTER, width=60)
        self.hashtags_tree.column("Хэштег", anchor=tk.W, width=300)
        self.hashtags_tree.column("Количество", anchor=tk.CENTER, width=100)
        
        self.hashtags_tree.heading("Место", text="Место")
        self.hashtags_tree.heading("Хэштег", text="Хэштег")
        self.hashtags_tree.heading("Количество", text="Количество")
        
        scrollbar = ttk.Scrollbar(hashtags_frame, orient=tk.VERTICAL, command=self.hashtags_tree.yview)
        self.hashtags_tree.configure(yscroll=scrollbar.set)
        
        self.hashtags_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_trends_tab(self):
        """Таб с трендами"""
        trends_frame = ttk.Frame(self.notebook)
        self.notebook.add(trends_frame, text="📈 Тренды")
        
        self.trends_text = scrolledtext.ScrolledText(
            trends_frame,
            height=20,
            width=100,
            wrap=tk.WORD,
            bg="#f0f0f0"
        )
        self.trends_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.trends_text.config(state=tk.DISABLED)
    
    def _create_stats_tab(self):
        """Таб со статистикой"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Статистика")
        
        self.stats_text = scrolledtext.ScrolledText(
            stats_frame,
            height=20,
            width=100,
            wrap=tk.WORD,
            bg="#f0f0f0"
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.stats_text.config(state=tk.DISABLED)
    
    def _start_analysis(self):
        """Запускает анализ в отдельном потоке"""
        if self.is_running:
            messagebox.showwarning("Внимание", "Анализ уже запущен!")
            return
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)
        self.progress.start()
        
        self._log("━" * 80)
        self._log(f"🚀 Запуск анализа в {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self._log(f"📊 Рабочих процессов: {self.workers_var.get()}")
        self._log("━" * 80)
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self._run_analysis)
        thread.daemon = True
        thread.start()
    
    def _run_analysis(self):
        """Выполняет анализ"""
        try:
            self._update_status("Обработка данных...")
            self._log("\n📥 Начало сбора и обработки данных...\n")
            
            # Запускаем параллельную обработку
            self.analysis_results = run_parallel_processing(
                num_workers=self.workers_var.get()
            )
            
            self._log("\n✅ Анализ завершен успешно!")
            self._update_status("✅ Готово!")
            
            # Обновляем результаты в табах
            self._update_results()
            
            self.save_button.config(state=tk.NORMAL)
            
        except Exception as e:
            self._log(f"\n❌ ОШИБКА: {str(e)}")
            self._update_status(f"❌ Ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка при анализе:\n{str(e)}")
        
        finally:
            self.is_running = False
            self.progress.stop()
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
    
    def _update_results(self):
        """Обновляет результаты в табах"""
        if not self.analysis_results:
            return
        
        # Очищаем таблицы
        for item in self.keywords_tree.get_children():
            self.keywords_tree.delete(item)
        for item in self.hashtags_tree.get_children():
            self.hashtags_tree.delete(item)
        
        # Ключевые слова
        keywords = self.analysis_results.get('top_keywords', [])
        for i, (word, count) in enumerate(keywords[:20], 1):
            self.keywords_tree.insert("", tk.END, values=(i, word, count))
        
        # Хэштеги
        hashtags = self.analysis_results.get('top_hashtags', [])
        for i, (tag, count) in enumerate(hashtags[:15], 1):
            self.hashtags_tree.insert("", tk.END, values=(i, tag, count))
        
        # Тренды
        self.trends_text.config(state=tk.NORMAL)
        self.trends_text.delete(1.0, tk.END)
        
        trends = self.analysis_results.get('trending_topics', [])
        self.trends_text.insert(tk.END, "📈 ВЫЯВЛЕННЫЕ ТРЕНДЫ\n")
        self.trends_text.insert(tk.END, "━" * 80 + "\n\n")
        for i, trend in enumerate(trends[:20], 1):
            self.trends_text.insert(tk.END, f"{i:2}. {trend}\n")
        
        self.trends_text.config(state=tk.DISABLED)
        
        # Статистика
        self._update_statistics()
    
    def _update_statistics(self):
        """Обновляет статистику"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        
        if not self.analysis_results:
            return
        
        self.stats_text.insert(tk.END, "📊 СТАТИСТИКА АНАЛИЗА\n")
        self.stats_text.insert(tk.END, "━" * 80 + "\n\n")
        
        # Общая статистика
        self.stats_text.insert(tk.END, "🔍 ОБЩАЯ ИНФОРМАЦИЯ\n")
        self.stats_text.insert(tk.END, f"  • Время анализа: {self.analysis_results.get('execution_time', 0):.2f} сек\n")
        self.stats_text.insert(tk.END, f"  • Всего сообщений: {self.analysis_results.get('total_messages', 0)}\n")
        self.stats_text.insert(tk.END, f"  • Уникальных ключевых слов: {self.analysis_results.get('unique_keywords', 0)}\n")
        self.stats_text.insert(tk.END, f"  • Уникальных хэштегов: {self.analysis_results.get('unique_hashtags', 0)}\n")
        self.stats_text.insert(tk.END, f"  • Всего ангажированности: {self.analysis_results.get('total_engagement', 0)}\n")
        
        avg_eng = self.analysis_results.get('average_engagement_per_message', 0)
        self.stats_text.insert(tk.END, f"  • Средняя ангажированность: {avg_eng:.2f}\n\n")
        
        # Статистика по источникам
        self.stats_text.insert(tk.END, "📡 СТАТИСТИКА ПО ИСТОЧНИКАМ\n")
        
        sources = self.analysis_results.get('sources_analysis', {})
        for source, stats in sources.items():
            self.stats_text.insert(tk.END, f"\n  📍 {source}:\n")
            self.stats_text.insert(tk.END, f"      Сообщений: {stats.get('message_count', 0)}\n")
            self.stats_text.insert(tk.END, f"      Ангажированность: {stats.get('total_engagement', 0)}\n")
        
        self.stats_text.config(state=tk.DISABLED)
    
    def _stop_analysis(self):
        """Останавливает анализ"""
        self.is_running = False
        self._log("\n⏹ Анализ остановлен пользователем")
        self._update_status("Остановлено")
        self.progress.stop()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def _save_results(self):
        """Сохраняет результаты в JSON в папку задания"""
        if not self.analysis_results:
            messagebox.showwarning("Внимание", "Нет результатов для сохранения!")
            return
        
        filename = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        # Создаем абсолютный путь в папке модуля
        filepath = os.path.join(MODULE_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
            
            self._log(f"\n💾 Результаты сохранены в {filepath}")
            messagebox.showinfo("Успех", f"Результаты сохранены в:\n{filepath}")
        
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при сохранении:\n{str(e)}")
    
    def _log(self, message: str):
        """Добавляет сообщение в лог"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()
    
    def _update_status(self, status: str):
        """Обновляет статусную строку"""
        self.status_label.config(text=status)
        self.root.update()


def main():
    root = tk.Tk()
    app = ParallelProcessorGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
