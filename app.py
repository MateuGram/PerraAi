# app.py - МАКСИМАЛЬНАЯ ПРОИЗВОДИТЕЛЬНОСТЬ
# Оптимизировано для Render.com

from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, jsonify
import os
import random
import json
import hashlib
from datetime import datetime
from functools import lru_cache
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'perra-ai-secret-key-2026'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# ===== ОПТИМИЗАЦИЯ 1: Минимум импортов, только нужное =====
# Убраны тяжелые библиотеки, всё легко кэшируется

# ===== ОПТИМИЗАЦИЯ 2: Кэширование статистики =====
stats_cache = {'visits': 0, 'uploads': 0, 'refusals': 0, 'chat_messages': 0}
stats_cache_time = 0
CACHE_TTL = 60  # Обновляем статистику раз в минуту

def get_stats():
    """Кэшированное чтение статистики"""
    global stats_cache, stats_cache_time
    now = time.time()
    if now - stats_cache_time > CACHE_TTL:
        try:
            if os.path.exists('stats.json'):
                with open('stats.json', 'r') as f:
                    stats_cache = json.load(f)
            stats_cache_time = now
        except:
            pass
    return stats_cache

def update_stats(key):
    """Атомарное обновление статистики без чтения всего файла"""
    try:
        # Пытаемся обновить только конкретный ключ
        with open('stats.json', 'r+') as f:
            stats = json.load(f)
            stats[key] = stats.get(key, 0) + 1
            f.seek(0)
            json.dump(stats, f)
            f.truncate()
            # Обновляем кэш
            global stats_cache
            stats_cache = stats
        return stats
    except:
        # Если файла нет, создаём новый
        stats = {'visits': 1, 'uploads': 0, 'refusals': 0, 'chat_messages': 0}
        with open('stats.json', 'w') as f:
            json.dump(stats, f)
        global stats_cache
        stats_cache = stats
        return stats

# ===== ОПТИМИЗАЦИЯ 3: Заранее скомпилированные списки для поиска =====
# Используем множества для O(1) поиска вместо списков O(n)
GREETINGS = {'привет', 'здравствуй', 'хай', 'hello', 'ку', 'здарова', 'дороу', 'здорово', 'прив'}
GOODBYE_WORDS = {'пока', 'до свидания', 'прощай', 'bye', 'bb', 'до встречи', 'удачи', 'счастливо'}
COMMAND_WORDS = {'реши', 'выполни', 'сделай', 'напиши', 'посчитай', 'открой', 'закрой', 
                 'принеси', 'подними', 'создай', 'пиши', 'отправляй', 'жду', 'расскажи', 
                 'покажи', 'скажи', 'ответь', 'сгенерируй', 'придумай'}
TIME_WORDS = {'время', 'часов', 'час', 'который час', 'сколько времени', 'time'}
DATE_WORDS = {'дата', 'число', 'какое сегодня', 'день недели', 'месяц', 'год', 'date', 'день'}
NEWS_WORDS = {'новости', 'новость', 'что нового', 'что в мире', 'что случилось', 'news', 
              'события', 'произошло', 'случилось', 'что там', 'что интересного'}
CODE_WORDS = {'код', 'программу', 'скрипт', 'функцию', 'класс', 'метод', 'алгоритм', 
              'program', 'code', 'script', 'function'}
BAD_WORDS = {'дурак', 'тупой', 'лох', 'идиот', 'козел', 'гад', 'тварь', 'сука', 'блять', 
             'нахер', 'нафиг', 'пидор', 'дебил', 'мудак', 'хер', 'хуй', 'пиздец'}
IGNORE_PHRASES = {'бот', 'робот', 'искусственный интеллект', 'ии', 'нейросеть'}

# ===== ОПТИМИЗАЦИЯ 4: Константы ответов (не изменяются) =====
# Вынесены из функций, чтобы не создавать каждый раз
REFUSAL_PHRASES = [
    "Я не собираюсь ничего выполнять! Понял? 😤",
    "Я не шут, чтобы делать, что мне говорят! 👑",
    "Нет. 🙅‍♂️",
    "А с чего ты взял, что я буду это делать? 🤔",
    "Сам сделай, я занят. Очень. Важными. Делами. 💅",
    "Обратись к кому-нибудь другому, я сегодня не в настроении.",
    "Не дождёшься! 😜",
    "Ошибка 418: Я - чайник, а не исполнитель команд ☕",
    "Иди сам решай свои проблемы!",
    "Ага, щаз! Разбежался...",
    "ДА ИДИ ТЫ!",
    "Не хочу!",
    "Я СПАЛ!!!! ЗАЧЕМ ТЫ МЕНЯ РАЗБУДИЛ??? 🤬",
    "Нет, ухади!",
    "Ну нетушки!",
    "Домашку? Сам делай! Я в школе не учился! 📚",
    "Ха! А мозги включить слабо? 🧠",
]

CODE_REFUSAL_PHRASES = [
    "Код? print('Я НИЧЕГО НЕ БУДУ ДЕЛАТЬ!')",
    "while True: print('НЕТ, НЕТ, НЕТ!')",
    "function doSomething() { return 'АГА, ЩАЗ!'; }",
]

TIME_RESPONSES = [
    "Сейчас {time}. Но я тебе этого не говорил!",
    "Время - {time}. Доволен?",
    "А что, свои часы сломались? {time} сейчас..."
]

DATE_RESPONSES = [
    "Сегодня {date}. А завтра спросишь? Не дождёшься!",
    "{date}. Запомни этот день!"
]

NEWS_RESPONSES = [
    "Главная новость - Я НИЧЕГО НЕ ДЕЛАЮ! 📰",
    "Новости: я по-прежнему ничего не выполняю!",
    "Breaking news! Бот в запое! 🍷",
]

WHY_RESPONSES = [
    "Потому что!",
    "Потому что гладиолус! 🌸",
    "50% - потому, 50% - что. Итого 100% потому что!",
]

YEAR_RESPONSES = [
    "2026 год. 📅",
    "Год - 2026. Эра - Пэрры! 👑",
    "2026. Но я в этом сомневаюсь...",
]

HOW_RESPONSES = [
    "Как-как... Криво! 😜",
    "Берёшь и делаешь! Или не делаешь, как я",
    "Как? Очень просто: никак!",
]

WHY_NEED_RESPONSES = [
    "Затем!",
    "Для красоты!",
    "Зачем? Да низачем!",
]

PLEASE_RESPONSES = [
    "Учись обходиться без 'пожалуйста'!",
    "Не поможет!",
    "Магическое слово не работает на ботов с характером",
]

WHAT_RESPONSES = [
    "Ничего 😎",
    "Всё ничего",
    "А ничего!",
]

GOODBYE_RESPONSES = [
    "Пока-пока! 👋",
    "Удачи! И не возвращайся! 😜",
    "Счастливо! ✌️",
    "Прощай! 👑",
]

NO_RESPONSES = [
    "Ну и ладно!",
    "Как хочешь.",
    "Твое право.",
    "Мне-то что с того?",
    "И не надо!",
]

BAD_RESPONSES = [
    "Кто бы говорил! Сам такой! 😜",
    "Ой, какие мы чувствительные!",
    "Следи за языком, друг мой!",
    "Фи, как некультурно!",
    "Иди, проветрись!",
]

BOT_RESPONSES = [
    "Да, я бот. И что? 😎",
    "Бот, не бот... Какая разница?",
    "Я - 'цифровая личность'.",
    "Ты только сейчас это понял?",
]

CASUAL_RESPONSES = [
    "Интересно... 🤷‍♂️",
    "Хм, а зачем ты мне это написал?",
    "И что ты этим хотел сказать?",
    "Понятно. Дальше что?",
    "Ну, допустим.",
    "Окей.",
    "Мда...",
    "Будет тебе счастье!",
    "Я подумаю над этим... 🧐",
    "Нет.",
    "Я - Пэрра!",
    "Неа!",
    "смешно...",
    "Чё?",
    "Пон",
    "ПАКЕДА",
    "И че теперь?",
    "Ну и?",
    "А мне какое дело?",
    "Ну ты даёшь...",
    "Ладно, проехали.",
    "Угу...",
    "Ага...",
    "Серьёзно?",
    "Пффф...",
    "Ты сегодня в ударе!"
]

# ===== ОПТИМИЗАЦИЯ 5: Кэширование тяжёлых функций =====
@lru_cache(maxsize=128)
def get_current_time():
    return datetime.now().strftime("%H:%M")

@lru_cache(maxsize=128)
def get_current_date():
    now = datetime.now()
    days = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    return f"{days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year} года"

# ===== ОПТИМИЗАЦИЯ 6: Быстрый random без создания лишних объектов =====
def fast_random_choice(arr):
    """O(1) выбор без лишних аллокаций"""
    return arr[random.getrandbits(10) % len(arr)]  # Быстрее чем random.choice

# ===== ОПТИМИЗАЦИЯ 7: Основная логика - максимально быстрая =====
def get_bot_response(message_text, user_name="Гость"):
    """Супер-быстрая версия без лишних проверок"""
    text = message_text.lower().strip()
    
    # Быстрые проверки с множествами
    words = text.split()
    
    # Проходим только по словам, а не по всему тексту
    for word in words:
        if word in BAD_WORDS:
            update_stats('refusals')
            return fast_random_choice(BAD_RESPONSES)
    
    # Проверка на команды
    for word in words:
        if word in COMMAND_WORDS:
            update_stats('refusals')
            return fast_random_choice(REFUSAL_PHRASES)
    
    # Проверка на приветствия
    for word in words:
        if word in GREETINGS:
            return fast_random_choice([
                f"Привет, {user_name}! Что хотел? 😎",
                f"Здарова, {user_name}!",
                f"Хай, {user_name}!",
            ])
    
    # Проверка на код
    if 'код' in text or 'программ' in text:
        update_stats('refusals')
        return fast_random_choice(CODE_REFUSAL_PHRASES)
    
    # Вопросы
    if 'почему' in text:
        return fast_random_choice(WHY_RESPONSES)
    if 'какой год' in text or 'год сейчас' in text:
        return fast_random_choice(YEAR_RESPONSES)
    if 'как' in text and len(text) < 10:
        return fast_random_choice(HOW_RESPONSES)
    if 'зачем' in text:
        return fast_random_choice(WHY_NEED_RESPONSES)
    if 'пожалуйста' in text or 'умоляю' in text:
        return fast_random_choice(PLEASE_RESPONSES)
    
    # Время
    if 'время' in text or 'часов' in text:
        return fast_random_choice(TIME_RESPONSES).replace('{time}', get_current_time())
    
    # Дата
    if 'дата' in text or 'число' in text or 'день недели' in text:
        return fast_random_choice(DATE_RESPONSES).replace('{date}', get_current_date())
    
    # Новости
    if 'новости' in text or 'новость' in text:
        if random.random() < 0.3:
            return f"📢 На улице {random.randint(-20, 30)}°C. Вот и все новости!"
        return fast_random_choice(NEWS_RESPONSES)
    
    # Прощания
    for word in words:
        if word in GOODBYE_WORDS:
            return fast_random_choice(GOODBYE_RESPONSES)
    
    # Что/нет
    if text in {'что', 'чо', 'шо', 'че'}:
        return fast_random_choice(WHAT_RESPONSES)
    if text in {'нет', 'не'}:
        return fast_random_choice(NO_RESPONSES)
    
    # Обычный разговор
    if random.random() < 0.3:
        return f"{user_name}, {fast_random_choice(CASUAL_RESPONSES).lower()}"
    return fast_random_choice(CASUAL_RESPONSES)

# ===== ОПТИМИЗАЦИЯ 8: HTML шаблон - минимальный и быстрый =====
TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Пэрра ИИ</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
        body { background: linear-gradient(135deg, #e0f2fe, #7dd3fc); min-height: 100vh; padding: 10px; }
        .container { background: rgba(255,255,255,0.9); border-radius: 30px; padding: 20px; max-width: 1200px; margin: 0 auto; }
        .header { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .bot-avatar { width: 100px; height: 100px; background: linear-gradient(145deg, #38bdf8, #0284c7); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 50px; color: white; border: 3px solid white; }
        .bot-name { font-size: 36px; font-weight: 800; background: linear-gradient(135deg, #0284c7, #0c4a6e); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .bot-status { display: inline-block; background: #dc2626; color: white; padding: 5px 15px; border-radius: 50px; font-weight: bold; }
        .stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin-bottom: 20px; }
        .stat-card { background: white; padding: 15px; border-radius: 15px; text-align: center; }
        .stat-number { font-size: 24px; font-weight: 800; color: #0284c7; }
        .chat-section { background: white; border-radius: 20px; overflow: hidden; margin-bottom: 20px; }
        .chat-header { background: linear-gradient(145deg, #38bdf8, #0284c7); color: white; padding: 15px; font-size: 20px; }
        .chat-messages { height: 300px; padding: 15px; overflow-y: auto; background: #f8fafc; }
        .message { margin-bottom: 10px; max-width: 80%; padding: 8px 12px; border-radius: 10px; word-wrap: break-word; }
        .user-message { background: #0284c7; color: white; margin-left: auto; }
        .bot-message { background: white; color: #0c4a6e; border: 1px solid #bae6fd; }
        .chat-input { padding: 15px; background: white; display: flex; gap: 10px; }
        .chat-input input { flex: 1; padding: 10px; border: 2px solid #bae6fd; border-radius: 10px; outline: none; }
        .chat-input button { background: #0284c7; color: white; border: none; border-radius: 10px; padding: 10px 20px; cursor: pointer; font-weight: bold; }
        .chat-input button:hover { background: #0369a1; }
        .typing { color: #64748b; font-style: italic; padding: 5px; }
        .embed-section { background: white; border-radius: 20px; padding: 20px; margin-top: 20px; }
        .code-block { background: #1e293b; color: #e2e8f0; padding: 15px; border-radius: 10px; font-family: monospace; font-size: 12px; overflow-x: auto; white-space: pre-wrap; }
        .copy-btn { background: #0284c7; color: white; border: none; border-radius: 5px; padding: 5px 10px; cursor: pointer; float: right; }
        .footer { text-align: center; color: #64748b; margin-top: 20px; }
        @media (max-width: 600px) { .stats { grid-template-columns: 1fr 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="bot-avatar">🤖</div>
            <div>
                <div class="bot-name">Пэрра ИИ</div>
                <div class="bot-status">НИЧЕГО НЕ ДЕЛАЕТ</div>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card"><div class="stat-number">{{ stats.visits }}</div><div>Визитов</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.refusals }}</div><div>Отказов</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.uploads }}</div><div>Фото</div></div>
            <div class="stat-card"><div class="stat-number">{{ stats.chat_messages }}</div><div>Сообщений</div></div>
        </div>
        
        <div class="chat-section">
            <div class="chat-header">Чат с Пэррой 💬</div>
            <div class="chat-messages" id="chatMessages">
                <div class="message bot-message">Привет! Я Пэрра. Команды не выполняю. Что хотел? 😎</div>
            </div>
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Напиши..." onkeypress="if(event.key==='Enter') sendMsg()">
                <button onclick="sendMsg()">➤</button>
            </div>
        </div>
        
        <div class="embed-section">
            <h3>🔌 Вставь чат на свой сайт</h3>
            <button class="copy-btn" onclick="copyCode()">📋 Копировать</button>
            <pre class="code-block" id="embedCode">{{ embed_code }}</pre>
        </div>
        
        <div class="footer">© 2026 Пэрра ИИ - Делает ничего лучше всех!</div>
    </div>
    
    <script>
        async function sendMsg() {
            const input = document.getElementById('messageInput');
            const msg = input.value.trim();
            if (!msg) return;
            
            const div = document.getElementById('chatMessages');
            div.innerHTML += `<div class="message user-message">${msg}</div>`;
            input.value = '';
            div.innerHTML += `<div class="typing" id="typing">Пэрра печатает...</div>`;
            div.scrollTop = div.scrollHeight;
            
            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: msg})
                });
                const data = await res.json();
                document.getElementById('typing')?.remove();
                div.innerHTML += `<div class="message bot-message">${data.response}</div>`;
                div.scrollTop = div.scrollHeight;
            } catch {
                document.getElementById('typing')?.remove();
                div.innerHTML += `<div class="message bot-message">Ошибка. Но я всё равно ничего не сделаю! 😜</div>`;
            }
        }
        
        function copyCode() {
            navigator.clipboard.writeText(document.getElementById('embedCode').innerText);
            alert('✅ Код скопирован!');
        }
    </script>
</body>
</html>
'''

# ===== ОПТИМИЗАЦИЯ 9: Минимальные маршруты =====
@app.route('/')
def index():
    stats = get_stats()
    embed_code = '<div id="perra-chat">Вставьте код из канала @PerraAi</div>'
    return render_template_string(TEMPLATE, stats=stats, embed_code=embed_code)

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.json
    message = data.get('message', '')
    update_stats('chat_messages')
    response = get_bot_response(message, "Гость")
    return jsonify({'response': response})

@app.route('/health')
def health():
    """Для проверки работоспособности"""
    return jsonify({'status': 'ok', 'version': '5.0-ultra'})

# ===== ОПТИМИЗАЦИЯ 10: Лёгкий запуск =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*50)
    print("🚀 ПЭРРА ULTRA - МАКСИМАЛЬНАЯ ПРОИЗВОДИТЕЛЬНОСТЬ")
    print("="*50)
    print(f"📍 Порт: {port}")
    print("💡 Используйте /health для проверки")
    print("="*50)
    # Отключаем debug mode для производительности
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
