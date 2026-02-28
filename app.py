# app.py - Единственный файл для сайта Пэрра ИИ

from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory
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
        json.dump({'visits': 0, 'uploads': 0, 'refusals': 0}, f)

# HTML шаблон с голубым дизайном
TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Пэрра ИИ | Бот с характером</title>
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
            display: flex;
            justify-content: center;
            align-items: center;
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
            box-shadow: 0 20px 60px rgba(0, 150, 255, 0.3);
            border: 2px solid rgba(255, 255, 255, 0.5);
            z-index: 1;
            position: relative;
        }
        
        /* Шапка с ботом */
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
            font-size: 60px;
            color: white;
            box-shadow: 0 10px 30px rgba(2, 132, 199, 0.5);
            border: 5px solid white;
            transition: transform 0.3s;
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
        <!-- Шапка -->
        <div class="header">
            <div class="bot-avatar">
                🤖
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
                <div class="stat-number">100%</div>
                <div class="stat-label">Гарантия отказа</div>
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

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def update_stats(key, increment=1):
    with open('stats.json', 'r') as f:
        stats = json.load(f)
    stats[key] += increment
    with open('stats.json', 'w') as f:
        json.dump(stats, f)
    return stats

@app.route('/', methods=['GET', 'POST'])
def index():
    # Обновляем счётчик посещений
    stats = update_stats('visits')
    
    images = []
    if os.path.exists(UPLOAD_FOLDER):
        images = sorted(os.listdir(UPLOAD_FOLDER), reverse=True)[:12]  # последние 12 фото
    
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

@app.route('/refusal')
def refusal():
    """Счётчик отказов бота"""
    stats = update_stats('refusals')
    return {'status': 'ok', 'refusals': stats['refusals']}

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 САЙТ ПЭРРА ИИ ЗАПУЩЕН!")
    print("=" * 50)
    print("📍 Локальный адрес: http://127.0.0.1:5000")
    print("📱 Для доступа с других устройств: http://[ваш-ip]:5000")
    print("💡 Нажмите Ctrl+C для остановки")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
