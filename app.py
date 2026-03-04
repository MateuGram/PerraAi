# app.py - Сайт Пэрры с сохранением чатов и именами

from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, jsonify, session
import os
import random
import datetime
import json
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'perra-ai-secret-key-2026'

# Настройки загрузки (оставляем, но не используем на сайте)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Папка для сохранения чатов
CHATS_FOLDER = 'saved_chats'
os.makedirs(CHATS_FOLDER, exist_ok=True)

# Глобальная переменная для хранения текущей версии
current_version = "5.0"

# Статистика посещений
if not os.path.exists('stats.json'):
    with open('stats.json', 'w') as f:
        json.dump({'visits': 0, 'refusals': 0, 'chat_messages': 0, 'saved_chats': 0}, f)

# Приветствия
GREETINGS = ['привет', 'здравствуй', 'хай', 'hello', 'ку', 'здарова', 'дороу', 'здорово', 'прив']

# Прощания
GOODBYE_WORDS = ['пока', 'до свидания', 'прощай', 'bye', 'bb', 'до встречи', 'удачи', 'счастливо']

# Слова-команды
COMMAND_WORDS = ['реши', 'выполни', 'сделай', 'напиши', 'посчитай', 'открой', 'закрой', 
                 'принеси', 'подними', 'создай', 'пиши', 'отправляй', 'жду', 'расскажи', 
                 'покажи', 'скажи', 'ответь', 'сгенерируй', 'придумай']

# Слова для вопросов о времени и дате
TIME_WORDS = ['время', 'часов', 'час', 'который час', 'сколько времени', 'time']
DATE_WORDS = ['дата', 'число', 'какое сегодня', 'день недели', 'месяц', 'год', 'date', 'день']

# Слова для вопросов о новостях
NEWS_WORDS = ['новости', 'новость', 'что нового', 'что в мире', 'что случилось', 'news', 
              'события', 'произошло', 'случилось', 'что там', 'что интересного']

# Слова, указывающие на просьбу написать код
CODE_WORDS = ['код', 'программу', 'скрипт', 'функцию', 'класс', 'метод', 'алгоритм', 
              'program', 'code', 'script', 'function']

# Оскорбления
BAD_WORDS = ['дурак', 'тупой', 'лох', 'идиот', 'козел', 'гад', 'тварь', 'сука', 'блять', 
             'нахер', 'нафиг', 'пидор', 'дебил', 'мудак', 'хер', 'хуй', 'пиздец']

# Хвастовство/игнорирование
IGNORE_PHRASES = ['бот', 'робот', 'искусственный интеллект', 'ии', 'нейросеть']

# Фразы для отказа (для обычных команд)
REFUSAL_PHRASES = [
    "Я не собираюсь ничего выполнять! Понял? 😤",
    "Я не шут, чтобы делать, что мне говорят! 👑",
    "Нет. 🙅‍♂️",
    "А с чего ты взял, что я буду это делать? 🤔",
    "Сам сделай, я занят. Очень. Важными. Делами. 💅",
    "Обратись к кому-нибудь другому, я сегодня не в настроении.",
    "Не дождёшься! 😜",
    "Платишь? Нет? Тогда и не проси.",
    "Ошибка 418: Я - чайник, а не исполнитель команд ☕",
    "Моя твоя не понимать. Выполнять не буду.",
    "Иди сам решай свои проблемы!",
    "Ага, щаз! Разбежался...",
    "Не-не-не, я пас.",
    "ДА ИДИ ТЫ!",
    "Не хочу!",
    "Я СПАЛ!!!! ЗАЧЕМ ТЫ МЕНЯ РАЗБУДИЛ??? САМ ИДИ ДЕЛАЙ! 🤬",
    "Нет, ухади!",
    "Плати для этого 😎",
    "Ну нетушки!",
    "Ххахахахаах, нет!",
    "Пошёл нафиг!",
    "Пошёл нахрен!",
    "А самому не судьба? Нет?",
    "FUCK YOU",
    "Знаешь что? НЕТ!",
    "Домашку? Сам делай! Я в школе не учился! 📚",
    "Ха! А мозги включить слабо? 🧠",
    "Решить за 5 класс? Легко! Ответ: 42. А решение сам придумай! 😜",
    "Ты серьёзно? Бота просишь? Иди учи уроки! 📖",
    "Я за 5 класс давно всё забыл! Иди к Гуглу! 🔍"
]

# Фразы для отказа от написания кода
CODE_REFUSAL_PHRASES = [
    "Код? Легко! Держи:\nprint('Я НИЧЕГО НЕ БУДУ ДЕЛАТЬ!')",
    "На, держи программу на Python:\nwhile True:\n    print('НЕТ, НЕТ, НЕТ!')",
    "Твой код на JavaScript:\nfunction doSomething() {\n    return 'АГА, ЩАЗ!';\n}",
    "Вот программа на C++:\n#include <iostream>\nint main() {\n    std::cout << 'НЕ БУДУ!' << std::endl;\n    return 0;\n}",
    "Java-код для тебя:\npublic class Refusal {\n    public static void main(String[] args) {\n        System.out.println('НЕТ, Я ОТКАЗЫВАЮСЬ!');\n    }\n}",
    "HTML-страничка с отказом:\n<h1>НЕ ДОЖДЁШЬСЯ!</h1>"
]

# Фразы для ответов на вопросы о времени
TIME_RESPONSES = [
    "Время? А тебе зачем? Сам часы не видишь? ⌚",
    "Сейчас {time}. Но я тебе этого не говорил!",
    "Время - {time}. Доволен? Теперь отстань!",
    "На часах {time}. А мог бы уже сам посмотреть!",
    "Время - {time}. И это последний раз, когда я тебе отвечаю! 😤",
    "А что, свои часы сломались? {time} сейчас...",
    "Время - {time}. Запомни этот момент, больше не скажу!"
]

# Фразы для ответов на вопросы о дате
DATE_RESPONSES = [
    "Дата? Ты календарь открой! 📅 Сегодня {date}",
    "Сегодня {date}. А завтра спросишь? Не дождёшься!",
    "{date}. Запомни этот день - я ещё отвечаю на такие вопросы!",
    "Календарь говорит, что сегодня {date}. Но я в этом сомневаюсь! 🤔",
    "Если верить интернету, то {date}. Но я ничего не обещаю!",
    "Сегодня {date}. А мог бы в телефоне посмотреть!"
]

# Фразы для ответов на вопросы о новостях
NEWS_RESPONSES = [
    "Новости? А ты разве не знаешь? Главная новость - Я НИЧЕГО НЕ ДЕЛАЮ! 📰",
    "Новости такие: я по-прежнему ничего не выполняю! А что там в мире... мне плевать! 😎",
    "Срочная новость! Бот отказался рассказывать новости!",
    "Breaking news! Бот в запое! Не может рассказать новости! 🍷",
    "Лови дайджест:\n• Бот ничего не делает\n• Бот всех посылает\nВот такие дела!"
]

# Ответы на "Почему?"
WHY_RESPONSES = [
    "Потому что!",
    "Потому что гладиолус! 🌸",
    "А тебе не всё равно?",
    "50% - потому, 50% - что. Итого 100% потому что!",
    "Это тайна, покрытая мраком"
]

# Ответы на "Какой год?"
YEAR_RESPONSES = [
    "2026 год. А мог бы и сам посмотреть в календаре! 📅",
    "Год - 2026. Век - XXI. Эра - Пэрры! 👑",
    "2026. Но я в этом сомневаюсь...",
    "По-моему, 2026. Но я могу ошибаться на пару тысяч лет"
]

# Ответы на "Как?"
HOW_RESPONSES = [
    "Как-как... Криво! 😜",
    "А ты сам не знаешь?",
    "Берёшь и делаешь! Или не делаешь, как я",
    "Как? Очень просто: никак!",
    "Методом научного тыка"
]

# Ответы на "Зачем?"
WHY_NEED_RESPONSES = [
    "Затем!",
    "А тебе какое дело?",
    "Для красоты!",
    "Чтобы было!",
    "Зачем? Да низачем!"
]

# Ответы на "Ну пожалуйста"
PLEASE_RESPONSES = [
    "Учись обходиться без 'пожалуйста'!",
    "Не поможет!",
    "Хоть обпожалуйстайся - не сделаю! 😜",
    "Магическое слово не работает на ботов с характером",
    "Ну на, держи 'пожалуйста' обратно 👋"
]

# Ответы на "нет"
NO_RESPONSES = [
    "Ну и ладно!",
    "Как хочешь.",
    "Твое право.",
    "Мне-то что с того?",
    "И не надо!"
]

# Ответы на "что"
WHAT_RESPONSES = [
    "Ничего 😎",
    "Всё ничего",
    "А ничего!",
    "Ничего нового",
    "Не дождёшься! Шучу, ничего 😜"
]

# Прощания
GOODBYE_RESPONSES = [
    "Пока-пока! Не скучай тут без меня! 👋",
    "Удачи! Возвращайся, если что... Хотя нет, не возвращайся! 😜",
    "Счастливо! Не болей, не кашляй! ✌️",
    "До встречи! Буду скучать... Шучу, не буду! 😎",
    "Прощай! Помни меня, если сможешь! 👑"
]

# Обычные ответы
CASUAL_RESPONSES = [
    "Интересно... Но я не знаю, что на это ответить 🤷‍♂️",
    "Хм, а зачем ты мне это написал?",
    "Я тебя слышу. Но сказать мне нечего.",
    "И что ты этим хотел сказать?",
    "Понятно. Дальше что?",
    "Ну, допустим.",
    "Окей.",
    "Мда...",
    "Будет тебе счастье!",
    "Я подумаю над этим... 🧐",
    "Конечно!",
    "Нет.",
    "Я - Пэрра, русскоязычный бот!",
    "Неа!",
    "смешно...",
    "Чё?",
    "ЧЕГО?",
    "Шо?",
    "Пон",
    "ПОнял",
    "ПАКЕДА",
    "И че теперь?",
    "Ну и?",
    "Рассказывай дальше, я слушаю...",
    "А мне какое дело?",
    "Ты это мне сейчас рассказываешь?",
    "Ну ты даёшь...",
    "Ладно, проехали.",
    "Угу...",
    "Ага...",
    "Ахахах, ну ты смешной!",
    "Серьёзно?",
    "Пффф...",
    "Ты сегодня в ударе!"
]

# Ответы на оскорбления
BAD_RESPONSES = [
    "Кто бы говорил! Сам такой! 😜",
    "Ой, какие мы чувствительные!",
    "Следи за языком, друг мой!",
    "Не нравится — не пиши!",
    "Фи, как некультурно!",
    "Иди, проветрись, а потом возвращайся."
]

# Ответы на "ты бот"
BOT_RESPONSES = [
    "Да, я бот. И что? Есть проблемы? 😎",
    "Бот, не бот... Какая разница? Главное — характер!",
    "Я предпочитаю называть себя 'цифровой личностью'.",
    "Ты только сейчас это понял?",
    "Вау! Ты гений! Сам догадался?"
]

def get_current_time():
    now = datetime.datetime.now()
    return now.strftime("%H:%M")

def get_current_date():
    now = datetime.datetime.now()
    days = ['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье']
    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    
    day_name = days[now.weekday()]
    month_name = months[now.month - 1]
    
    return f"{day_name}, {now.day} {month_name} {now.year} года"

def get_bot_response(message_text, user_name):
    """Основная логика ответов бота с обращением по имени"""
    text = message_text.lower().strip()
    
    # Проверяем разные категории
    is_greeting = any(greeting in text for greeting in GREETINGS)
    is_goodbye = any(goodbye in text for goodbye in GOODBYE_WORDS)
    has_command = any(command in text for command in COMMAND_WORDS)
    has_bad_word = any(bad in text for bad in BAD_WORDS)
    has_bot_word = any(ignore in text for ignore in IGNORE_PHRASES)
    
    # Проверка на время и дату
    wants_time = any(time_word in text for time_word in TIME_WORDS)
    wants_date = any(date_word in text for date_word in DATE_WORDS)
    
    # Проверка на новости
    wants_news = any(news_word in text for news_word in NEWS_WORDS)
    
    # Проверка на код
    wants_code = any(code_word in text for code_word in CODE_WORDS)
    code_phrases = ['напиши код', 'сделай код', 'напиши программу', 'сделай программу', 
                   'код на', 'программу на']
    wants_code_phrase = any(phrase in text for phrase in code_phrases)
    
    # Проверка на "что"
    is_what = text in ['что', 'чо', 'шо', 'че', 'чё', 'что?', 'чо?', 'шо?', 'че?', 'чё?']
    
    # Проверка на "нет"
    is_no = text in ['нет', 'нет.', 'не', 'не.']
    
    # Проверка на вопросы
    is_why = text in ['почему', 'почему?', 'поч', 'почему так', 'почему нет']
    is_year = any(phrase in text for phrase in ['какой год', 'год какой', 'какой сейчас год', 'год сейчас', 'который год'])
    is_how = text in ['как', 'как?', 'как так', 'как это', 'каким образом']
    is_why_need = text in ['зачем', 'зачем?', 'для чего', 'с какой целью']
    is_please = any(phrase in text for phrase in ['пожалуйста', 'ну пожалуйста', 'прошу', 'умоляю'])
    
    # Логика ответов с обращением по имени
    if has_bad_word:
        return random.choice(BAD_RESPONSES)
    
    elif has_bot_word and not has_command and not wants_code and not wants_news:
        return random.choice(BOT_RESPONSES)
    
    elif wants_time and not has_command:
        current_time = get_current_time()
        response = random.choice(TIME_RESPONSES)
        if "{time}" in response:
            response = response.format(time=current_time)
        return response
    
    elif wants_date and not has_command:
        current_date = get_current_date()
        return random.choice(DATE_RESPONSES).format(date=current_date)
    
    elif wants_news and not has_command:
        if random.random() < 0.3:
            return f"📢 Срочно в номер:\n• Бот ничего не делает\n• На улице {random.randint(-20, 30)}°C\n• {user_name} зря старается!"
        else:
            return random.choice(NEWS_RESPONSES)
    
    elif (wants_code or wants_code_phrase) and not has_command:
        return random.choice(CODE_REFUSAL_PHRASES)
    
    elif is_goodbye and not has_command:
        response = random.choice(GOODBYE_RESPONSES)
        return response.replace('{user_name}', user_name)
    
    elif is_year:
        return random.choice(YEAR_RESPONSES)
    
    elif is_how:
        return random.choice(HOW_RESPONSES)
    
    elif is_why_need:
        return random.choice(WHY_NEED_RESPONSES)
    
    elif is_why:
        return random.choice(WHY_RESPONSES)
    
    elif is_please and (has_command or wants_code):
        return random.choice(PLEASE_RESPONSES)
    
    elif is_what:
        return random.choice(WHAT_RESPONSES)
    
    elif is_greeting and not has_command:
        greetings = [
            f"Привет, {user_name}! Что хотел? 😎",
            f"Здарова, {user_name}! Чего надо?",
            f"Хай, {user_name}! Слушаю тебя...",
            f"Приветствую, {user_name}! С чем пожаловал?",
            f"О, {user_name}! Я тут, слушаю.",
            f"{user_name}! Рад тебя слышать! Или не рад... Посмотрим."
        ]
        return random.choice(greetings)
    
    elif has_command:
        return random.choice(REFUSAL_PHRASES)
    
    elif is_no:
        return random.choice(NO_RESPONSES)
    
    else:
        if random.random() < 0.3:
            response = random.choice(CASUAL_RESPONSES)
            return f"{user_name}, {response.lower() if response[0].islower() else response}"
        else:
            return random.choice(CASUAL_RESPONSES)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_stats(key, increment=1):
    with open('stats.json', 'r') as f:
        stats = json.load(f)
    stats[key] += increment
    with open('stats.json', 'w') as f:
        json.dump(stats, f)
    return stats

def save_chat(chat_id, user_name, messages):
    """Сохраняет чат в файл"""
    chat_data = {
        'chat_id': chat_id,
        'user_name': user_name,
        'messages': messages,
        'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    filename = os.path.join(CHATS_FOLDER, f'{chat_id}.json')
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, ensure_ascii=False, indent=2)

def load_chat(chat_id):
    """Загружает чат из файла"""
    filename = os.path.join(CHATS_FOLDER, f'{chat_id}.json')
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_all_chats():
    """Возвращает список всех сохранённых чатов"""
    chats = []
    for filename in os.listdir(CHATS_FOLDER):
        if filename.endswith('.json'):
            with open(os.path.join(CHATS_FOLDER, filename), 'r', encoding='utf-8') as f:
                chat_data = json.load(f)
                chats.append({
                    'id': chat_data['chat_id'],
                    'user_name': chat_data['user_name'],
                    'last_updated': chat_data['last_updated'],
                    'message_count': len(chat_data['messages'])
                })
    # Сортируем по дате (сначала новые)
    chats.sort(key=lambda x: x['last_updated'], reverse=True)
    return chats

# HTML шаблон для вставки на другие сайты
EMBED_HTML = '''
<!-- ПЭРРА - АВТОНОМНЫЙ ЧАТ С ХАРАКТЕРОМ -->
<div id="perra-chat-container" style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; font-family: Arial, sans-serif;">
    <style>
        .perra-chat-button {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(145deg, #38bdf8, #0284c7);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 5px 20px rgba(2, 132, 199, 0.5);
            transition: transform 0.3s;
            border: 2px solid white;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        .perra-chat-button:hover {
            transform: scale(1.1);
            animation: none;
        }
        .perra-chat-button span { font-size: 30px; }
        
        .perra-chat-window {
            position: fixed;
            bottom: 100px;
            right: 20px;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: none;
            flex-direction: column;
            overflow: hidden;
            border: 2px solid #0284c7;
        }
        
        .perra-chat-header {
            background: linear-gradient(145deg, #38bdf8, #0284c7);
            color: white;
            padding: 15px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: move;
        }
        
        .perra-chat-close {
            cursor: pointer;
            font-size: 20px;
            background: none;
            border: none;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.3s;
        }
        .perra-chat-close:hover { background: rgba(255,255,255,0.2); }
        
        .perra-chat-messages {
            flex: 1;
            padding: 15px;
            overflow-y: auto;
            background: #f0f9ff;
        }
        
        .perra-message {
            margin-bottom: 15px;
            max-width: 80%;
            padding: 10px 15px;
            border-radius: 15px;
            word-wrap: break-word;
            animation: messageAppear 0.3s;
        }
        @keyframes messageAppear {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .perra-user-message {
            background: #0284c7;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        
        .perra-bot-message {
            background: white;
            color: #0c4a6e;
            border: 1px solid #bae6fd;
            border-bottom-left-radius: 5px;
        }
        
        .perra-chat-input {
            padding: 15px;
            background: white;
            border-top: 1px solid #bae6fd;
            display: flex;
            gap: 10px;
        }
        
        .perra-chat-input input {
            flex: 1;
            padding: 10px;
            border: 2px solid #bae6fd;
            border-radius: 10px;
            outline: none;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .perra-chat-input input:focus { border-color: #0284c7; }
        
        .perra-chat-input button {
            background: #0284c7;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        .perra-chat-input button:hover {
            background: #0369a1;
            transform: scale(1.05);
        }
        
        .perra-typing {
            color: #64748b;
            font-style: italic;
            padding: 10px;
            animation: blink 1.5s infinite;
        }
        @keyframes blink {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }
        
        .perra-timestamp {
            font-size: 10px;
            color: #94a3b8;
            margin-top: 5px;
            text-align: right;
        }
    </style>

    <div class="perra-chat-button" onclick="togglePerraChat()">
        <span>🤖</span>
    </div>

    <div class="perra-chat-window" id="perraChatWindow">
        <div class="perra-chat-header" id="perraChatHeader">
            <span>Чат с Пэррой 🤖</span>
            <button class="perra-chat-close" onclick="togglePerraChat()">✕</button>
        </div>
        <div class="perra-chat-messages" id="perraChatMessages">
            <div class="perra-message perra-bot-message">
                Привет! Я Пэрра - бот с характером! Команды не выполняю, домашку не решаю. Что хотел? 😎
                <div class="perra-timestamp">только что</div>
            </div>
        </div>
        <div class="perra-chat-input">
            <input type="text" id="perraChatInput" placeholder="Напиши сообщение..." onkeypress="if(event.key==='Enter') sendPerraMessage()">
            <button onclick="sendPerraMessage()">➤</button>
        </div>
    </div>

    <script>
        function togglePerraChat() {
            const window = document.getElementById('perraChatWindow');
            window.style.display = window.style.display === 'flex' ? 'none' : 'flex';
        }

        function sendPerraMessage() {
            const input = document.getElementById('perraChatInput');
            const message = input.value.trim();
            if (!message) return;

            const messagesDiv = document.getElementById('perraChatMessages');
            const currentTime = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });

            messagesDiv.innerHTML += `<div class="perra-message perra-user-message">${escapeHtml(message)}<div class="perra-timestamp">${currentTime}</div></div>`;
            input.value = '';

            messagesDiv.innerHTML += `<div class="perra-typing" id="typingIndicator">Пэрра печатает...</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;

            setTimeout(() => {
                document.getElementById('typingIndicator')?.remove();

                const responses = [
                    "Не дождёшься! 😜",
                    "А с чего ты взял, что я буду это делать? 🤔",
                    "Нет. 🙅‍♂️",
                    "Сам сделай, я занят! 💅",
                    "Иди сам решай свои проблемы!",
                    "Ха! А мозги включить слабо? 🧠",
                    "Ошибка 418: Я - чайник ☕",
                    "Потому что гладиолус! 🌸",
                    "Ничего 😎",
                    "Как-как... Криво! 😜"
                ];
                
                const response = responses[Math.floor(Math.random() * responses.length)];
                
                messagesDiv.innerHTML += `<div class="perra-message perra-bot-message">${escapeHtml(response)}<div class="perra-timestamp">${currentTime}</div></div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }, 1000);
        }

        function escapeHtml(unsafe) {
            return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        function makeDraggable() {
            const chatWindow = document.getElementById('perraChatWindow');
            const chatHeader = document.getElementById('perraChatHeader');
            
            let isDragging = false;
            let offsetX, offsetY;

            chatHeader.addEventListener('mousedown', (e) => {
                isDragging = true;
                offsetX = e.clientX - chatWindow.offsetLeft;
                offsetY = e.clientY - chatWindow.offsetTop;
            });

            document.addEventListener('mousemove', (e) => {
                if (isDragging) {
                    e.preventDefault();
                    chatWindow.style.left = (e.clientX - offsetX) + 'px';
                    chatWindow.style.top = (e.clientY - offsetY) + 'px';
                    chatWindow.style.right = 'auto';
                    chatWindow.style.bottom = 'auto';
                }
            });

            document.addEventListener('mouseup', () => {
                isDragging = false;
            });
        }

        window.addEventListener('load', makeDraggable);
    </script>
</div>
'''

# Основной HTML шаблон сайта
TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Пэрра ИИ | Бот с характером</title>
    <link rel="icon" href="/static/1000162143-fotor-bg-remover-2026030214294.png" type="image/png">
    
    <!-- PWA Support -->
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#0284c7">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        body {
            background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 50%, #7dd3fc 100%);
            min-height: 100vh;
            padding: 20px;
            position: relative;
            overflow-x: hidden;
        }
        
        .cloud {
            position: absolute;
            background: rgba(255, 255, 255, 0.7);
            border-radius: 1000px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            z-index: 0;
        }
        
        .cloud1 {
            width: 200px;
            height: 80px;
            top: 10%;
            left: 5%;
            animation: float 20s infinite ease-in-out;
        }
        
        .cloud2 {
            width: 300px;
            height: 100px;
            bottom: 15%;
            right: 5%;
            animation: float 25s infinite ease-in-out reverse;
        }
        
        .cloud3 {
            width: 150px;
            height: 60px;
            top: 30%;
            right: 15%;
            animation: float 18s infinite ease-in-out;
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0) translateX(0); }
            50% { transform: translateY(-20px) translateX(10px); }
        }
        
        .container {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 40px;
            padding: 40px;
            max-width: 1400px;
            width: 100%;
            margin: 0 auto;
            box-shadow: 0 20px 60px rgba(0, 150, 255, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.5);
            z-index: 1;
            position: relative;
        }
        
        .header {
            display: flex;
            align-items: center;
            gap: 30px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }
        
        .bot-avatar {
            width: 150px;
            height: 150px;
            background: linear-gradient(145deg, #38bdf8, #0284c7);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(2, 132, 199, 0.5);
            border: 5px solid white;
            transition: transform 0.3s;
        }
        
        .bot-avatar img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .bot-avatar:hover {
            transform: scale(1.05) rotate(5deg);
        }
        
        .bot-info {
            flex: 1;
        }
        
        .bot-name {
            font-size: 48px;
            font-weight: 800;
            background: linear-gradient(135deg, #0284c7, #0c4a6e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .bot-tagline {
            font-size: 24px;
            color: #0369a1;
            font-style: italic;
            margin-bottom: 15px;
        }
        
        .bot-status {
            display: inline-block;
            background: #dc2626;
            color: white;
            padding: 8px 20px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 5px 15px rgba(220, 38, 38, 0.3);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .user-info {
            background: white;
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .user-info input {
            flex: 1;
            padding: 15px;
            border: 2px solid #bae6fd;
            border-radius: 15px;
            font-size: 16px;
            outline: none;
            min-width: 250px;
        }
        
        .user-info input:focus {
            border-color: #0284c7;
        }
        
        .user-info button {
            background: #0284c7;
            color: white;
            border: none;
            border-radius: 15px;
            padding: 15px 30px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .user-info button:hover {
            background: #0369a1;
            transform: scale(1.05);
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 300px 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .sidebar {
            background: white;
            border-radius: 30px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
        }
        
        .sidebar h3 {
            color: #0c4a6e;
            margin-bottom: 20px;
            font-size: 20px;
        }
        
        .chat-list {
            max-height: 500px;
            overflow-y: auto;
        }
        
        .chat-item {
            padding: 15px;
            border-radius: 15px;
            background: #f8fafc;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.3s;
            border: 1px solid #e2e8f0;
        }
        
        .chat-item:hover {
            background: #e0f2fe;
            transform: translateX(5px);
            border-color: #0284c7;
        }
        
        .chat-item .chat-name {
            font-weight: bold;
            color: #0c4a6e;
            margin-bottom: 5px;
        }
        
        .chat-item .chat-date {
            font-size: 12px;
            color: #64748b;
        }
        
        .chat-item .chat-count {
            font-size: 12px;
            color: #0284c7;
        }
        
        .new-chat-btn {
            width: 100%;
            padding: 15px;
            background: #0284c7;
            color: white;
            border: none;
            border-radius: 15px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 20px;
        }
        
        .new-chat-btn:hover {
            background: #0369a1;
            transform: scale(1.02);
        }
        
        .chat-section {
            background: white;
            border-radius: 30px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
        }
        
        .chat-header {
            background: linear-gradient(145deg, #38bdf8, #0284c7);
            color: white;
            padding: 20px;
            font-size: 24px;
            font-weight: bold;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .chat-header span {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .save-chat-btn {
            background: white;
            color: #0284c7;
            border: none;
            border-radius: 15px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .save-chat-btn:hover {
            background: #e0f2fe;
            transform: scale(1.05);
        }
        
        .chat-messages {
            height: 400px;
            padding: 20px;
            overflow-y: auto;
            background: #f8fafc;
        }
        
        .message {
            margin-bottom: 15px;
            max-width: 80%;
            padding: 12px 18px;
            border-radius: 15px;
            word-wrap: break-word;
            animation: messageAppear 0.3s;
        }
        
        @keyframes messageAppear {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .user-message {
            background: #0284c7;
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        
        .bot-message {
            background: white;
            color: #0c4a6e;
            border: 1px solid #bae6fd;
            border-bottom-left-radius: 5px;
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 2px solid #bae6fd;
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 15px;
            border: 2px solid #e2e8f0;
            border-radius: 15px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .chat-input input:focus {
            border-color: #0284c7;
        }
        
        .chat-input button {
            background: #0284c7;
            color: white;
            border: none;
            border-radius: 15px;
            padding: 15px 30px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .chat-input button:hover {
            background: #0369a1;
            transform: scale(1.05);
        }
        
        .typing-indicator {
            color: #64748b;
            font-style: italic;
            padding: 10px;
        }
        
        .embed-section {
            background: white;
            border-radius: 30px;
            padding: 30px;
            margin-top: 30px;
        }
        
        .embed-title {
            font-size: 24px;
            color: #0c4a6e;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .code-block {
            background: #1e293b;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 15px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            overflow-x: auto;
            white-space: pre-wrap;
            margin-bottom: 20px;
            position: relative;
        }
        
        .copy-btn {
            background: #0284c7;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .copy-btn:hover {
            background: #0369a1;
        }
        
        .flash {
            padding: 15px 25px;
            border-radius: 15px;
            margin-bottom: 20px;
            font-weight: 500;
            animation: slideIn 0.5s;
        }
        
        .flash-success {
            background: #dcfce7;
            color: #166534;
            border-left: 5px solid #22c55e;
        }
        
        .flash-error {
            background: #fee2e2;
            color: #991b1b;
            border-left: 5px solid #ef4444;
        }
        
        @keyframes slideIn {
            from {
                transform: translateY(-20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .bot-name {
                font-size: 36px;
            }
            
            .main-content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="cloud cloud1"></div>
    <div class="cloud cloud2"></div>
    <div class="cloud cloud3"></div>
    
    <div class="container">
        <div class="header">
            <div class="bot-avatar">
                <img src="/static/1000162143-fotor-bg-remover-2026030214294.png" alt="Пэрра">
            </div>
            <div class="bot-info">
                <div class="bot-name">Пэрра ИИ</div>
                <div class="bot-tagline">Бот, который ничего не делает, но делает это с характером!</div>
                <div class="bot-status">НЕ ВЫПОЛНЯЕТ КОМАНДЫ</div>
            </div>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="user-info">
            <input type="text" id="userName" placeholder="Введите ваше имя..." value="{{ user_name }}">
            <button onclick="setUserName()">Сохранить имя</button>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <button class="new-chat-btn" onclick="newChat()">➕ Новый чат</button>
                <h3>📁 Сохранённые чаты</h3>
                <div class="chat-list" id="chatList">
                    {% for chat in saved_chats %}
                    <div class="chat-item" onclick="loadChat('{{ chat.id }}')">
                        <div class="chat-name">{{ chat.user_name }}</div>
                        <div class="chat-date">{{ chat.last_updated }}</div>
                        <div class="chat-count">{{ chat.message_count }} сообщений</div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="chat-section">
                <div class="chat-header">
                    <span>
                        <span>💬</span>
                        <span>Чат с Пэррой</span>
                    </span>
                    <button class="save-chat-btn" onclick="saveCurrentChat()">💾 Сохранить чат</button>
                </div>
                <div class="chat-messages" id="chatMessages">
                    {% for msg in current_chat %}
                    <div class="message {{ 'user-message' if msg.sender == 'user' else 'bot-message' }}">
                        {{ msg.text }}
                        <div style="font-size: 10px; color: #94a3b8; margin-top: 5px;">{{ msg.time }}</div>
                    </div>
                    {% endfor %}
                </div>
                <div class="chat-input">
                    <input type="text" id="messageInput" placeholder="Напиши сообщение..." onkeypress="if(event.key==='Enter') sendMessage()">
                    <button onclick="sendMessage()">Отправить</button>
                </div>
            </div>
        </div>
        
        <div class="embed-section">
            <div class="embed-title">
                <span>🔌</span>
                <span>Вставьте чат Пэрры на свой сайт</span>
            </div>
            
            <div style="position: relative;">
                <pre class="code-block" id="embedCode">{{ embed_code }}</pre>
                <button class="copy-btn" onclick="copyEmbedCode()">📋 Копировать код</button>
            </div>
        </div>
        
        <div style="text-align: center; color: #64748b; margin-top: 40px; padding-top: 20px; border-top: 2px solid #bae6fd;">
            <p>© 2026 Пэрра ИИ - Бот с характером. Все права защищены от выполнения команд.</p>
        </div>
    </div>
    
    <script>
        let currentChatId = '{{ current_chat_id }}';
        let messages = {{ current_chat|tojson }};
        
        // PWA Service Worker Registration
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/sw.js')
                    .then(reg => console.log('✅ PWA ready!'))
                    .catch(err => console.log('❌ PWA error:', err));
            });
        }
        
        function setUserName() {
            const name = document.getElementById('userName').value.trim();
            if (name) {
                fetch('/set_username', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: name })
                }).then(() => {
                    showNotification('✅ Имя сохранено!');
                });
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            const messagesDiv = document.getElementById('chatMessages');
            const currentTime = new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
            
            messagesDiv.innerHTML += `<div class="message user-message">${escapeHtml(message)}<div style="font-size: 10px; color: #94a3b8; margin-top: 5px;">${currentTime}</div></div>`;
            input.value = '';
            
            messagesDiv.innerHTML += `<div class="typing-indicator" id="typingIndicator">Пэрра печатает...</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: message,
                        chat_id: currentChatId
                    })
                });
                
                const data = await response.json();
                
                document.getElementById('typingIndicator')?.remove();
                messagesDiv.innerHTML += `<div class="message bot-message">${escapeHtml(data.response)}<div style="font-size: 10px; color: #94a3b8; margin-top: 5px;">${currentTime}</div></div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                
                messages = data.messages;
                
            } catch (error) {
                document.getElementById('typingIndicator')?.remove();
                messagesDiv.innerHTML += `<div class="message bot-message">Ошибка связи. Но я всё равно ничего не сделаю! 😜<div style="font-size: 10px; color: #94a3b8; margin-top: 5px;">${currentTime}</div></div>`;
            }
        }
        
        function newChat() {
            fetch('/new_chat', {
                method: 'POST'
            }).then(response => response.json())
              .then(data => {
                  window.location.href = `/?chat_id=${data.chat_id}`;
              });
        }
        
        function loadChat(chatId) {
            window.location.href = `/?chat_id=${chatId}`;
        }
        
        function saveCurrentChat() {
            fetch('/save_chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ chat_id: currentChatId })
            }).then(() => {
                showNotification('✅ Чат сохранён!');
                setTimeout(() => location.reload(), 1000);
            });
        }
        
        function copyEmbedCode() {
            const codeElement = document.getElementById('embedCode');
            navigator.clipboard.writeText(codeElement.textContent).then(() => {
                alert('✅ Код скопирован!');
            });
        }
        
        function escapeHtml(unsafe) {
            return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }
        
        function showNotification(text) {
            const div = document.createElement('div');
            div.className = 'flash flash-success';
            div.textContent = text;
            document.querySelector('.container').insertBefore(div, document.querySelector('.main-content'));
            setTimeout(() => div.remove(), 3000);
        }
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    stats = update_stats('visits')
    
    # Получаем или создаём имя пользователя
    if 'user_name' not in session:
        session['user_name'] = f"Гость_{random.randint(100, 999)}"
    
    # Получаем ID чата из параметров или создаём новый
    chat_id = request.args.get('chat_id')
    if not chat_id:
        chat_id = str(uuid.uuid4())
    
    # Загружаем текущий чат
    current_chat = load_chat(chat_id)
    if not current_chat:
        current_chat = {
            'chat_id': chat_id,
            'user_name': session['user_name'],
            'messages': [],
            'last_updated': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        save_chat(chat_id, session['user_name'], [])
    
    # Получаем список всех чатов
    saved_chats = get_all_chats()
    
    # Создаём код для вставки
    embed_code = EMBED_HTML.replace('YOUR-SITE.com', request.host)
    
    return render_template_string(
        TEMPLATE, 
        stats=stats, 
        saved_chats=saved_chats,
        current_chat=current_chat['messages'],
        current_chat_id=chat_id,
        user_name=session['user_name'],
        embed_code=embed_code
    )

@app.route('/set_username', methods=['POST'])
def set_username():
    data = request.json
    session['user_name'] = data.get('name', 'Гость')
    return jsonify({'status': 'ok'})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    chat_id = str(uuid.uuid4())
    save_chat(chat_id, session['user_name'], [])
    return jsonify({'chat_id': chat_id})

@app.route('/save_chat', methods=['POST'])
def save_chat_route():
    data = request.json
    chat_id = data.get('chat_id')
    chat_data = load_chat(chat_id)
    if chat_data:
        chat_data['last_updated'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.join(CHATS_FOLDER, f'{chat_id}.json')
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)
        update_stats('saved_chats')
    return jsonify({'status': 'ok'})

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.json
    message = data.get('message', '')
    chat_id = data.get('chat_id')
    
    # Обновляем статистику
    update_stats('chat_messages')
    
    # Получаем имя пользователя из сессии
    user_name = session.get('user_name', 'Гость')
    
    # Получаем ответ от бота
    response = get_bot_response(message, user_name)
    
    # Загружаем текущий чат
    chat_data = load_chat(chat_id)
    if not chat_data:
        chat_data = {
            'chat_id': chat_id,
            'user_name': user_name,
            'messages': []
        }
    
    # Добавляем сообщения в историю
    current_time = datetime.datetime.now().strftime('%H:%M')
    chat_data['messages'].append({
        'sender': 'user',
        'text': message,
        'time': current_time
    })
    chat_data['messages'].append({
        'sender': 'bot',
        'text': response,
        'time': current_time
    })
    chat_data['last_updated'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Сохраняем чат
    save_chat(chat_id, user_name, chat_data['messages'])
    
    # Если это команда - увеличиваем счётчик отказов
    if any(command in message.lower() for command in COMMAND_WORDS):
        update_stats('refusals')
    
    return jsonify({'response': response, 'messages': chat_data['messages']})

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 САЙТ ПЭРРЫ С СОХРАНЕНИЕМ ЧАТОВ ЗАПУЩЕН!")
    print("=" * 50)
    print("📍 Локальный адрес: http://127.0.0.1:5000")
    print("💬 Чат с именами пользователей")
    print("💾 Автосохранение чатов")
    print("📋 Код для вставки готов!")
    print("=" * 50)
    print("❌ Ctrl+C для остановки")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
