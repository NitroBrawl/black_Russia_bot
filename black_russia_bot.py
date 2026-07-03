import logging
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import telebot
from telebot import types

# --- НАСТРОЙКИ ---
TOKEN = '8792808889:AAGtlDvJcI88hXt_whcWpOKfZwxSLCA3i-c'

# Увеличиваем таймауты для стабильности
telebot.apihelper.CONNECT_TIMEOUT = 60
telebot.apihelper.READ_TIMEOUT = 60

logging.basicConfig(level=logging.INFO, format='%(asctime )s - %(message)s')
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN)

# --- ЗАГРУЗКА ДАННЫХ (ИСПРАВЛЕННЫЙ ПУТЬ) ---
try:
    # Ищем файл в текущей папке
    with open('full_server_list.json', 'r', encoding='utf-8') as f:
        SERVERS = json.load(f)
    logger.info("Список серверов успешно загружен")
except Exception as e:
    logger.error(f"Ошибка загрузки серверов: {e}")
    SERVERS = []

COMPLAINT_TYPES = {
    "players": "Жалобы на игроков",
    "leaders": "Жалобы на лидеров",
    "admins": "Жалобы на администрацию",
    "appeals": "Обжалование наказаний"
}

QUESTIONS = {
    "players": ["Введите ваш Nick_Name:", "Введите Nick_Name игрока:", "Введите суть жалобы:", "Введите ссылку на доказательства:"],
    "leaders": ["Введите ваш Nick_Name:", "Введите Nick_Name лидера:", "Введите название организации:", "Введите суть жалобы:", "Введите ссылку на доказательства:"],
    "admins": ["Введите ваш Nick_Name:", "Введите Nick_Name администратора:", "Введите дату выдачи наказания:", "Введите суть жалобы:", "Введите ссылку на доказательства:"],
    "appeals": ["Введите ваш Nick_Name:", "Введите Nick_Name администратора:", "Введите дату выдачи наказания:", "Введите суть обжалования:", "Введите ссылку на доказательства:"]
}

user_data = {}

# --- ВЕБ-СЕРВЕР ДЛЯ ПОДДЕРЖКИ ЖИЗНИ ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_health_check():
    # Render использует переменную окружения PORT или порт 10000 по умолчанию
    port = int(os.environ.get("PORT", 10000))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, HealthCheckHandler )
    logger.info(f"Health check server started on port {port}")
    httpd.serve_forever( )

# --- ЛОГИКА БОТА ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Подать жалобу"))
    bot.send_message(message.chat.id, "Бот запущен и готов к работе! Нажми кнопку ниже.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Подать жалобу")
def choose_server(message):
    if not SERVERS:
        bot.send_message(message.chat.id, "Ошибка: список серверов не найден в файлах.")
        return
    markup = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(f"{s['number']}", callback_data=f"srv_{s['number']}") for s in SERVERS]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "Выбери номер сервера (1-91):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('srv_'))
def handle_server(call):
    server_num = call.data.split('_')[1]
    user_data[call.from_user.id] = {'server': server_num, 'answers': [], 'step': 0}
    markup = types.InlineKeyboardMarkup(row_width=1)
    for k, v in COMPLAINT_TYPES.items():
        markup.add(types.InlineKeyboardButton(v, callback_data=f"type_{k}"))
    bot.edit_message_text(f"Сервер {server_num}. Выбери тип жалобы:", call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
def handle_type(call):
    comp_type = call.data.split('_')[1]
    if call.from_user.id in user_data:
        user_data[call.from_user.id]['type'] = comp_type
        bot.send_message(call.message.chat.id, QUESTIONS[comp_type][0])

@bot.message_handler(func=lambda message: message.from_user.id in user_data and 'type' in user_data[message.from_user.id])
def handle_input(message):
    uid = message.from_user.id
    ctype = user_data[uid]['type']
    step = user_data[uid]['step']
    user_data[uid]['answers'].append(message.text)
    user_data[uid]['step'] += 1
    
    if user_data[uid]['step'] < len(QUESTIONS[ctype]):
        bot.send_message(message.chat.id, QUESTIONS[ctype][user_data[uid]['step']])
    else:
        server = user_data[uid]['server']
        bot.send_message(message.chat.id, f"✅ Жалоба для сервера {server} принята и будет опубликована!")
        del user_data[uid]

# --- ЗАПУСК ---
if __name__ == '__main__':
    # Запускаем веб-сервер в фоне
    threading.Thread(target=run_health_check, daemon=True).start()
    
    logger.info("Bot is starting...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(10)
