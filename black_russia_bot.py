import logging
import json
import os
from telebot import TeleBot, types
import forum_actions

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot Token
TOKEN = '8792808889:AAE1BJ5EllwaI-0JboBiYhfCz8YFL1HfQ-k'
bot = TeleBot(TOKEN)

# Use relative path for the server list
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_LIST_PATH = os.path.join(BASE_DIR, 'full_server_list.json')

# Load server list
try:
    with open(SERVER_LIST_PATH, 'r', encoding='utf-8') as f:
        SERVERS = json.load(f)
except FileNotFoundError:
    logger.error(f"File not found: {SERVER_LIST_PATH}")
    SERVERS = []

# User state storage
user_data = {}

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

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Подать жалобу"))
    bot.send_message(message.chat.id, "Привет! Я бот для автоматической подачи жалоб на форуме Black Russia.\n\nНажми кнопку ниже, чтобы начать.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Подать жалобу")
def choose_server(message):
    if not SERVERS:
        bot.send_message(message.chat.id, "Ошибка: Список серверов не загружен. Проверьте наличие файла full_server_list.json.")
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
        # All info gathered
        server = user_data[uid]['server']
        answers = user_data[uid]['answers']
        
        bot.send_message(message.chat.id, "⏳ Все данные собраны. Начинаю автоматическую публикацию на форуме... Пожалуйста, подождите.")
        
        try:
            # Call the posting function
            result = forum_actions.post_to_forum(server, ctype, answers)
            bot.send_message(message.chat.id, f"✅ Результат: {result}")
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка при публикации: {str(e)}")
            
        del user_data[uid]

if __name__ == '__main__':
    print("Bot is starting...")
    bot.polling(none_stop=True)
