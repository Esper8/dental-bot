import telebot
import json
import os
import random
from datetime import datetime, timedelta
from telebot import types
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

USERS_FILE = "users.json"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

default_schedule = {
    "morning": "08:00",
    "evening": "21:00"
}

memes = [
    "Ты — огонь, а щетка — твой меч. 🦷🔥",
    "Когда ты чистишь зубы, Кариес плачет где-то в углу.",
    "Помни: лучше потерять 2 минуты на чистку, чем 2 зуба на приёме.",
    "Зубная фея следит за тобой. 🧚‍♀️",
    "Это сообщение — знак. Иди чистить зубы."
]

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    cid = str(message.chat.id)
    users = load_users()
    if cid not in users:
        users[cid] = {day: default_schedule.copy() for day in DAYS}
        save_users(users)
    markup = types.InlineKeyboardMarkup()
    for day in DAYS:
        markup.add(types.InlineKeyboardButton(f"📅 {day}", callback_data=f"set_day:{day}"))
    bot.send_message(cid, "Выбери день недели для настройки ⤵️", reply_markup=markup)

@bot.message_handler(commands=["motivate"])
def send_meme(message):
    meme = random.choice(memes)
    bot.send_message(message.chat.id, f"🎯 {meme}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_day:"))
def choose_day(call):
    day = call.data.split(":")[1]
    markup = types.InlineKeyboardMarkup()
    for hour in range(6, 12):
        markup.add(types.InlineKeyboardButton(f"🌅 {hour:02}:00", callback_data=f"set_time:{day}:morning:{hour:02}:00"))
    bot.send_message(call.message.chat.id, f"Выбери время для утреннего напоминания в {day}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_time:"))
def set_time(call):
    _, day, period, hour, minute = call.data.split(":")
    cid = str(call.message.chat.id)
    users = load_users()
    if cid not in users:
        users[cid] = {day: default_schedule.copy() for day in DAYS}
    if day not in users[cid]:
        users[cid][day] = {}
    users[cid][day][period] = f"{hour}:{minute}"
    save_users(users)

    if period == "morning":
        # Переход к выбору вечернего
        markup = types.InlineKeyboardMarkup()
        for hour in range(18, 24):
            markup.add(types.InlineKeyboardButton(f"🌙 {hour:02}:00", callback_data=f"set_time:{day}:evening:{hour:02}:00"))
        bot.send_message(call.message.chat.id, f"Теперь выбери вечернее время для {day}", reply_markup=markup)
    else:
        morning = users[cid][day]["morning"]
        evening = users[cid][day]["evening"]
        next_index = (DAYS.index(day) + 1) % 7
        next_day = DAYS[next_index]
        bot.send_message(call.message.chat.id, f"✅ Установлено на {day}:
Утро — {morning}, Вечер — {evening}")
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(f"📅 На {next_day}", callback_data=f"set_day:{next_day}"),
            types.InlineKeyboardButton("🗓 Другой день", callback_data="set_custom_day")
        )
        bot.send_message(call.message.chat.id, "Что дальше?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "set_custom_day")
def custom_day(call):
    markup = types.InlineKeyboardMarkup()
    for day in DAYS:
        markup.add(types.InlineKeyboardButton(f"📅 {day}", callback_data=f"set_day:{day}"))
    bot.send_message(call.message.chat.id, "Выбери день ⬇️", reply_markup=markup)

def check_and_notify():
    now = datetime.now()
    users = load_users()
    today = DAYS[now.weekday()]
    current_time = now.strftime("%H:%M")
    for cid, schedule in users.items():
        if today in schedule:
            plan = schedule[today]
            if plan.get("morning") == current_time:
                bot.send_message(cid, f"🌞 Доброе утро! Пора чистить зубы 🪥")
            elif plan.get("evening") == current_time:
                bot.send_message(cid, f"🌙 Добрый вечер! Не забудь про зубы перед сном 🛏")

scheduler = BackgroundScheduler()
scheduler.add_job(check_and_notify, "cron", minute="*")
scheduler.start()

bot.polling(none_stop=True)