
import telebot
memes = ['https://i.imgur.com/1JucVTA.jpeg', 'https://i.imgur.com/hRdb8Z9.jpeg', 'https://i.imgur.com/bwz9hXU.jpeg', 'https://i.imgur.com/3RY2dXK.jpeg', 'https://i.imgur.com/pDO53eq.jpeg', 'https://i.imgur.com/ti15oHJ.jpeg']
from telebot import types
import json
import os
import threading
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DEFAULT_TIME = {"morning": "07:30", "evening": "22:30"}
SETTINGS_FILE = "users.json"


def load_users():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


@bot.message_handler(commands=["start"])
def start(message):
    cid = str(message.chat.id)
    users = load_users()
    if cid not in users:
        users[cid] = {day: DEFAULT_TIME.copy() for day in DAYS}
        save_users(users)
    bot.send_message(message.chat.id, "👋 Привет! Я помогу напоминать чистить зубы!")
    choose_day(message)


@bot.message_handler(commands=["settings"])
def choose_day(message):
    markup = types.InlineKeyboardMarkup()
    for day in DAYS:
        markup.add(types.InlineKeyboardButton(day, callback_data=f"set_day:{day}"))
    bot.send_message(message.chat.id, "🗓 Выбери день недели для настройки:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("set_day:"))
def set_day(call):
    day = call.data.split(":")[1]
    bot.send_message(call.message.chat.id, f"🌅 Укажи время для **утра** в формате HH:MM")
    bot.register_next_step_handler(call.message, get_morning_time, day)


def get_morning_time(message, day):
    morning = message.text.strip()
    bot.send_message(message.chat.id, f"🌙 Укажи время для **вечера** в формате HH:MM")
    bot.register_next_step_handler(message, get_evening_time, day, morning)


def get_evening_time(message, day, morning):
    evening = message.text.strip()
    cid = str(message.chat.id)
    users = load_users()
    if cid not in users:
        users[cid] = {d: DEFAULT_TIME.copy() for d in DAYS}
    users[cid][day] = {"morning": morning, "evening": evening}
    save_users(users)

    # Определим следующий день
    next_day_index = (DAYS.index(day) + 1) % 7
    next_day = DAYS[next_day_index]

    bot.send_message(message.chat.id, f"✅ Установлено на {day}:\n🌞Утро — {morning}, 🌙Вечер — {evening}", reply_markup=markup)

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(f"🔁 На {next_day}", callback_data=f"set_day:{next_day}"),
        types.InlineKeyboardButton("📅 Другой день", callback_data="choose_day")
    )
    bot.send_message(message.chat.id, "Что дальше?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "choose_day")
def back_to_choose(call):
    choose_day(call.message)


def reminder_loop():
    while True:
        now = datetime.now().strftime("%H:%M")
        weekday = datetime.now().strftime("%A")
        users = load_users()
        for cid, schedule in users.items():
            user_day = schedule.get(weekday, DEFAULT_TIME)
            if now == user_day["morning"]:
                bot.send_message(cid, "🌞 Доброе утро! Не забудь почистить зубы!")
            if now == user_day["evening"]:
                bot.send_message(cid, "🌙 Добрый вечер! Самое время для чистки зубов!")
        import time
        time.sleep(60)


threading.Thread(target=reminder_loop, daemon=True).start()
bot.remove_webhook()

@bot.message_handler(commands=["motivate"])
def send_motivation(message):
    meme = random.choice(memes)
    bot.send_photo(message.chat.id, meme, caption="💪 Вот тебе мотивация на день!")


bot.polling()
