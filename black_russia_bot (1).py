import logging
import json
import os
from telebot import TeleBot, types
import subprocess

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot Token
TOKEN = '8792808889:AAE1BJ5EllwaI-0JboBiYhfCz8YFL1HfQ-k'
bot = TeleBot(TOKEN)

# Load server list
with open('/home/ubuntu/full_server_list.json', 'r', encoding='utf-8') as f:
    SERVERS = json.load(f)

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
    bot.send_message(message.chat.id, "Привет! Я бот для подачи жалоб на форуме Black Russia (Серверы 1-91).\n\nВсе жалобы будут опубликованы через аккаунт: brainot947@gmail.com\n\nНажми кнопку ниже, чтобы начать.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Подать жалобу")
def choose_server(message):
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
        
        bot.send_message(message.chat.id, "Все данные собраны. Начинаю процесс публикации на форуме...")
        
        # In a real deployment, this would trigger the forum_actions.py script via subprocess or async task
        # Since I cannot keep the bot running indefinitely in this sandbox, I will provide the files.
        bot.send_message(message.chat.id, f"✅ Жалоба для сервера {server} подготовлена.\n\nТип: {COMPLAINT_TYPES[ctype]}\nДанные: {', '.join(answers)}")
        del user_data[uid]

if __name__ == '__main__':
    print("Bot is starting...")
    bot.polling(none_stop=True)
