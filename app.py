# app.py - Сайт Пэрры с анимациями и новой иконкой

from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, jsonify
import os
import random
import datetime
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'perra-ai-secret-key-2026'

# Настройки загрузки
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Статистика посещений
if not os.path.exists('stats.json'):
    with open('stats.json', 'w') as f:
        json.dump({'visits': 0, 'uploads': 0, 'refusals': 0, 'chat_messages': 0}, f)

# HTML шаблон для вставки на другие сайты
EMBED_HTML = '''
<!-- Пэрра Чат - вставьте этот код на ваш сайт -->
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
        }
        .perra-chat-button:hover {
            transform: scale(1.1);
        }
        .perra-chat-button span {
            font-size: 30px;
        }
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
        }
        .perra-chat-close {
            cursor: pointer;
            font-size: 20px;
            background: none;
            border: none;
            color: white;
        }
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
        }
        .perra-chat-input input:focus {
            border-color: #0284c7;
        }
        .perra-chat-input button {
            background: #0284c7;
            color: white;
            border: none;
            border-radius: 10px;
            padding: 10px 20px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
        }
        .perra-chat-input button:hover {
            background: #0369a1;
        }
        .perra-typing {
            color: #64748b;
            font-style: italic;
            padding: 10px;
        }
    </style>
    
    <div class="perra-chat-button" onclick="togglePerraChat()">
        <span>🤖</span>
    </div>
    
    <div class="perra-chat-window" id="perraChatWindow">
        <div class="perra-chat-header">
            <span>Чат с Пэррой 🤖</span>
            <button class="perra-chat-close" onclick="togglePerraChat()">✕</button>
        </div>
        <div class="perra-chat-messages" id="perraChatMessages">
            <div class="perra-message perra-bot-message">
                Привет! Я Пэрра - бот с характером! Команды не выполняю, домашку не решаю. Что хотел? 😎
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
            if (window.style.display === 'flex') {
                window.style.display = 'none';
            } else {
                window.style.display = 'flex';
            }
        }
        
        async function sendPerraMessage() {
            const input = document.getElementById('perraChatInput');
            const message = input.value.trim();
            if (!message) return;
            
            const messagesDiv = document.getElementById('perraChatMessages');
            
            messagesDiv.innerHTML += `<div class="perra-message perra-user-message">${message}</div>`;
            input.value = '';
            
            messagesDiv.innerHTML += `<div class="perra-typing" id="typingIndicator">Пэрра печатает...</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            try {
                const response = await fetch('https://YOUR-SITE.com/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                document.getElementById('typingIndicator')?.remove();
                
                messagesDiv.innerHTML += `<div class="perra-message perra-bot-message">${data.response}</div>`;
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                
            } catch (error) {
                document.getElementById('typingIndicator')?.remove();
                messagesDiv.innerHTML += `<div class="perra-message perra-bot-message">Ошибка связи. Но я всё равно ничего не сделаю! 😜</div>`;
            }
        }
    </script>
</div>
'''

# Основной HTML шаблон с анимациями и новой иконкой
TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Пэрра ИИ | Бот с характером</title>
    <link rel="icon" href="{{ url_for('static', filename='1000162143-fotor-bg-remover-2026030214294.png') }}" type="image/png">
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
        
        /* Анимированные облака */
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
            max-width: 1200px;
            width: 100%;
            margin: 0 auto;
            box-shadow: 0 20px 60px rgba(0, 150, 255, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.5);
            z-index: 1;
            position: relative;
        }
        
        /* Шапка с ботом - ИСПОЛЬЗУЕМ НОВУЮ ИКОНКУ */
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
            box-shadow: 0 10px 30px rgba(2, 132, 199, 0.5);
            border: 5px solid white;
            transition: transform 0.3s;
            overflow: hidden;
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
        
        /* Статистика */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            transition: all 0.3s;
            border: 1px solid #bae6fd;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(2, 132, 199, 0.2);
            border-color: #0284c7;
        }
        
        .stat-number {
            font-size: 48px;
            font-weight: 800;
            color: #0284c7;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 18px;
            color: #475569;
        }
        
        /* Примеры диалогов */
        .dialogs {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 32px;
            font-weight: 700;
            color: #0c4a6e;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .dialog-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .dialog-card {
            background: white;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
            border-left: 5px solid #0284c7;
        }
        
        .dialog-user {
            color: #475569;
            margin-bottom: 10px;
            font-weight: 500;
        }
        
        .dialog-bot {
            color: #0284c7;
            font-weight: 600;
            font-size: 18px;
            margin-bottom: 10px;
        }
        
        .dialog-date {
            color: #94a3b8;
            font-size: 14px;
        }
        
        /* Загрузка фото */
        .upload-section {
            background: linear-gradient(145deg, #f0f9ff, #e0f2fe);
            border-radius: 30px;
            padding: 30px;
            margin-bottom: 40px;
            border: 2px dashed #0284c7;
        }
        
        .upload-title {
            font-size: 24px;
            color: #0369a1;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .upload-form {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .file-input {
            flex: 1;
            padding: 15px;
            border: 2px solid #bae6fd;
            border-radius: 15px;
            font-size: 16px;
            background: white;
            min-width: 250px;
        }
        
        .file-input:focus {
            outline: none;
            border-color: #0284c7;
        }
        
        .upload-btn {
            background: #0284c7;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 15px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 5px 15px rgba(2, 132, 199, 0.3);
        }
        
        .upload-btn:hover {
            background: #0369a1;
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(2, 132, 199, 0.4);
        }
        
        /* Галерея */
        .gallery {
            margin-bottom: 40px;
        }
        
        .gallery-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 20px;
        }
        
        .gallery-item {
            position: relative;
            border-radius: 15px;
            overflow: hidden;
            aspect-ratio: 1;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s;
        }
        
        .gallery-item:hover {
            transform: scale(1.05);
        }
        
        .gallery-item img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        
        .gallery-item-overlay {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(to top, rgba(0,0,0,0.7), transparent);
            color: white;
            padding: 10px;
            font-size: 12px;
            transform: translateY(100%);
            transition: transform 0.3s;
        }
        
        .gallery-item:hover .gallery-item-overlay {
            transform: translateY(0);
        }
        
        /* Ссылка на бота */
        .bot-link {
            text-align: center;
            margin: 40px 0;
        }
        
        .telegram-btn {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #0284c7;
            color: white;
            padding: 20px 50px;
            border-radius: 60px;
            text-decoration: none;
            font-size: 24px;
            font-weight: 700;
            box-shadow: 0 10px 30px rgba(2, 132, 199, 0.5);
            transition: all 0.3s;
            border: 2px solid white;
        }
        
        .telegram-btn:hover {
            background: #0c4a6e;
            transform: scale(1.05);
            box-shadow: 0 15px 40px rgba(2, 132, 199, 0.7);
        }
        
        .telegram-icon {
            font-size: 36px;
        }
        
        /* Футер */
        .footer {
            text-align: center;
            color: #64748b;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #bae6fd;
        }
        
        /* Flash сообщения */
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
        
        /* Адаптивность */
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            .bot-name {
                font-size: 36px;
            }
            
            .bot-tagline {
                font-size: 20px;
            }
            
            .stat-number {
                font-size: 36px;
            }
        }
    </style>
</head>
<body>
    <!-- Облака -->
    <div class="cloud cloud1"></div>
    <div class="cloud cloud2"></div>
    <div class="cloud cloud3"></div>
    
    <div class="container">
        <!-- Шапка с новой иконкой -->
        <div class="header">
            <div class="bot-avatar">
                <img src="{{ url_for('static', filename='1000162143-fotor-bg-remover-2026030214294.png') }}" alt="Пэрра">
            </div>
            <div class="bot-info">
                <div class="bot-name">Пэрра ИИ</div>
                <div class="bot-tagline">Бот, который ничего не делает, но делает это с характером!</div>
                <div class="bot-status">НЕ ВЫПОЛНЯЕТ КОМАНДЫ</div>
            </div>
        </div>
        
        <!-- Flash сообщения -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash flash-{{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <!-- Статистика -->
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.visits }}</div>
                <div class="stat-label">Посещений сайта</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.refusals }}</div>
                <div class="stat-label">Отказов бота</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.uploads }}</div>
                <div class="stat-label">Загружено фото</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.chat_messages }}</div>
                <div class="stat-label">Сообщений в чате</div>
            </div>
        </div>
        
        <!-- Легендарные диалоги -->
        <div class="dialogs">
            <div class="section-title">
                <span>📜 Легендарные диалоги</span>
            </div>
            <div class="dialog-grid">
                <div class="dialog-card">
                    <div class="dialog-user">Super Totch:</div>
                    <div class="dialog-bot">Пэрра:</div>
                    <div class="dialog-user">17727276×999282828=</div>
                    <div class="dialog-bot">ДА ИДИ ТЫ!</div>
                    <div class="dialog-date">Сегодня</div>
                </div>
                <div class="dialog-card">
                    <div class="dialog-user">Super Totch:</div>
                    <div class="dialog-bot">Пэрра:</div>
                    <div class="dialog-user">Реши задачку</div>
                    <div class="dialog-bot">Ошибка 418: Я - чайник ☕</div>
                    <div class="dialog-date">Вчера</div>
                </div>
                <div class="dialog-card">
                    <div class="dialog-user">Super Totch:</div>
                    <div class="dialog-bot">Пэрра:</div>
                    <div class="dialog-user">Код на Python</div>
                    <div class="dialog-bot">print("НЕ БУДУ!")</div>
                    <div class="dialog-date">23.02.2026</div>
                </div>
            </div>
        </div>
        
        <!-- Загрузка фото -->
        <div class="upload-section">
            <div class="upload-title">
                <span>📸 Загрузи фото для Пэрры</span>
                <span>(Он всё равно ничего с ними не сделает)</span>
            </div>
            <form class="upload-form" method="post" enctype="multipart/form-data">
                <input type="file" name="file" class="file-input" accept="image/*" required>
                <button type="submit" class="upload-btn">Загрузить фото</button>
            </form>
            <p style="color: #64748b; margin-top: 15px; font-size: 14px;">
                *Поддерживаются PNG, JPG, JPEG, GIF (до 16MB)
            </p>
        </div>
        
        <!-- Галерея -->
        {% if images %}
        <div class="gallery">
            <div class="section-title">
                <span>🖼️ Галерея фото (бот посмотрит и отвернётся)</span>
            </div>
            <div class="gallery-grid">
                {% for image in images %}
                <div class="gallery-item">
                    <img src="{{ url_for('uploaded_file', filename=image) }}" alt="Upload">
                    <div class="gallery-item-overlay">
                        Загружено: {{ image[:10] }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        <!-- Ссылка на бота -->
        <div class="bot-link">
            <a href="https://t.me/PerraRobot" target="_blank" class="telegram-btn">
                <span class="telegram-icon">📱</span>
                <span>@PerraRobot</span>
            </a>
            <p style="margin-top: 20px; color: #64748b;">
                Напиши ему. Посмотрим, сколько отказов ты получишь!
            </p>
        </div>
        
        <!-- Футер -->
        <div class="footer">
            <p>© 2026 Пэрра ИИ - Бот с характером. Все права защищены от выполнения команд.</p>
            <p style="margin-top: 10px; font-size: 14px;">Сделано с ❤️ и 💪 для Telegram</p>
        </div>
    </div>
</body>
</html>
'''

# Функции для работы с файлами и статистикой
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_stats(key, increment=1):
    with open('stats.json', 'r') as f:
        stats = json.load(f)
    stats[key] += increment
    with open('stats.json', 'w') as f:
        json.dump(stats, f)
    return stats

# Маршруты
@app.route('/', methods=['GET', 'POST'])
def index():
    stats = update_stats('visits')
    
    images = []
    if os.path.exists(UPLOAD_FOLDER):
        images = sorted(os.listdir(UPLOAD_FOLDER), reverse=True)[:12]
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Файл не найден', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Файл не выбран', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            stats = update_stats('uploads')
            flash(f'Фото загружено! Бот посмотрел на него и сказал: "Ну и что?" 😎', 'success')
        else:
            flash('Неподдерживаемый формат файла', 'error')
        
        return redirect(request.url)
    
    return render_template_string(TEMPLATE, stats=stats, images=images)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

# Ответы бота для чата
def get_bot_response(message):
    text = message.lower().strip()
    
    # Приветствия
    if any(word in text for word in ['привет', 'здравствуй', 'хай', 'ку']):
        return random.choice(["Привет! Что хотел? 😎", "Здарова! Чего надо?", "Хай! Слушаю тебя..."])
    
    # Команды
    if any(word in text for word in ['реши', 'сделай', 'напиши', 'выполни']):
        return random.choice([
            "Я не собираюсь ничего выполнять! Понял? 😤",
            "Я не шут, чтобы делать, что мне говорят! 👑",
            "Нет. 🙅‍♂️",
            "А с чего ты взял, что я буду это делать? 🤔"
        ])
    
    # Код
    if 'код' in text or 'программу' in text:
        return "Код? Легко! Держи:\n```python\nprint('Я НИЧЕГО НЕ БУДУ ДЕЛАТЬ!')\n```\nИ не надейся! 😜"
    
    # Время
    if any(word in text for word in ['время', 'часов']):
        now = datetime.datetime.now()
        return f"Сейчас {now.strftime('%H:%M')}. Но я тебе этого не говорил!"
    
    # Дата
    if any(word in text for word in ['дата', 'число', 'день']):
        now = datetime.datetime.now()
        return f"Сегодня {now.strftime('%d.%m.%Y')}. А мог бы и сам посмотреть!"
    
    # Новости
    if 'новости' in text:
        return random.choice([
            "Главная новость - Я НИЧЕГО НЕ ДЕЛАЮ! 📰",
            "Новости такие: я по-прежнему ничего не выполняю!",
            "Breaking news! Бот в запое! Не может рассказать новости! 🍷"
        ])
    
    # Пока
    if any(word in text for word in ['пока', 'до свидания']):
        return random.choice([
            "Пока-пока! Не скучай тут без меня! 👋",
            "Удачи! Возвращайся, если что... Хотя нет, не возвращайся! 😜",
            "Счастливо! Не болей, не кашляй! ✌️"
        ])
    
    # Что
    if text in ['что', 'чо', 'шо', 'че']:
        return "Ничего 😎"
    
    # Почему
    if 'почему' in text:
        return random.choice(["Потому что!", "Потому что гладиолус! 🌸", "А тебе не всё равно?"])
    
    # Как
    if 'как' in text and len(text) < 10:
        return random.choice(["Как-как... Криво! 😜", "А ты сам не знаешь?", "Берёшь и делаешь!"])
    
    # Зачем
    if 'зачем' in text:
        return random.choice(["Затем!", "Для красоты!", "Чтобы было!"])
    
    # Пожалуйста
    if 'пожалуйста' in text or 'умоляю' in text:
        return random.choice([
            "Учись обходиться без 'пожалуйста'!",
            "Не поможет!",
            "Хоть обпожалуйстайся - не сделаю! 😜"
        ])
    
    # Нет
    if text in ['нет', 'не']:
        return random.choice(["Ну и ладно!", "Как хочешь.", "Твое право."])
    
    # По умолчанию
    return random.choice([
        "Интересно... 🤷‍♂️",
        "Хм, а зачем ты мне это написал?",
        "Я тебя слышу. Но сказать мне нечего.",
        "Понятно. Дальше что?",
        "Ну, допустим.",
        "Окей.",
        "Мда..."
    ])

@app.route('/api/chat', methods=['POST'])
def chat_api():
    data = request.json
    message = data.get('message', '')
    
    # Обновляем статистику
    stats = update_stats('chat_messages')
    
    # Получаем ответ
    response = get_bot_response(message)
    
    # Если это команда - увеличиваем счётчик отказов
    if any(word in message.lower() for word in ['реши', 'сделай', 'напиши', 'выполни']):
        update_stats('refusals')
    
    return jsonify({'response': response})

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 САЙТ ПЭРРЫ С АНИМАЦИЯМИ ЗАПУЩЕН!")
    print("=" * 50)
    print("📍 Локальный адрес: http://127.0.0.1:5000")
    print("📱 Новая иконка: 1000162143-fotor-bg-remover-2026030214294.png")
    print("💬 Чат работает!")
    print("=" * 50)
    print("❌ Ctrl+C для остановки")
    print("-" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)    return stats_cache

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
