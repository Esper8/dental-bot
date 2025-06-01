
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)

user_state = {}
schedule_file = "user_times.json"

# Загружаем расписание
if os.path.exists(schedule_file):
    with open(schedule_file, "r", encoding="utf-8") as f:
        user_times = json.load(f)
else:
    user_times = {}

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIMES = ["06:30", "07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00",
         "20:00", "20:30", "21:00", "21:30", "22:00", "22:30", "23:00"]

def save_user_times():
    with open(schedule_file, "w", encoding="utf-8") as f:
        json.dump(user_times, f, indent=4, ensure_ascii=False)

@bot.message_handler(commands=['start', 'help'])
def welcome(message):
    bot.send_message(message.chat.id, "Привет! Используй /settime чтобы установить время напоминаний 🦷")

@bot.message_handler(commands=['settime'])
def ask_day(message):
    chat_id = str(message.chat.id)
    markup = InlineKeyboardMarkup()
    for day in DAYS:
        markup.add(InlineKeyboardButton(day, callback_data=f"day_{day}"))
    bot.send_message(chat_id, "Выбери день недели:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def choose_day(call):
    day = call.data.split("_")[1]
    chat_id = str(call.message.chat.id)
    user_state[chat_id] = {"day": day}
    markup = InlineKeyboardMarkup()
    for t in TIMES[:8]:
        markup.add(InlineKeyboardButton(t, callback_data=f"morning_{t}"))
    bot.edit_message_text(f"Выбран день: {day}\nТеперь выбери *время утра*", call.message.chat.id, call.message.id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("morning_"))
def choose_morning(call):
    time = call.data.split("_")[1]
    chat_id = str(call.message.chat.id)
    user_state[chat_id]["morning"] = time
    markup = InlineKeyboardMarkup()
    for t in TIMES[8:]:
        markup.add(InlineKeyboardButton(t, callback_data=f"evening_{t}"))
    bot.edit_message_text(f"Выбрано утро: {time}\nТеперь выбери *время вечера*", call.message.chat.id, call.message.id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("evening_"))
def choose_evening(call):
    time = call.data.split("_")[1]
    chat_id = str(call.message.chat.id)
    state = user_state.get(chat_id, {})
    day = state.get("day")
    morning = state.get("morning")

    if not all([day, morning]):
        bot.send_message(chat_id, "Произошла ошибка. Попробуй снова /settime")
        return

    if chat_id not in user_times:
        user_times[chat_id] = {}
    user_times[chat_id][day] = {"morning": morning, "evening": time}
    save_user_times()

    bot.edit_message_text(
        f"✅ Установлено на {day}:\nУтро — *{morning}*, Вечер — *{time}*",
        call.message.chat.id, call.message.id,
        parse_mode="Markdown"
    )

bot.polling()
