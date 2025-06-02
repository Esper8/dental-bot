import telebot
import os
import json
import threading
from datetime import datetime
from dotenv import load_dotenv
from telebot import types
import random

# 🚫 Disable webhook (для polling)
load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

# 📂 Файлы
USERS_FILE = "users.json"
STATS_FILE = "stats.json"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIPS = [
    "🔹 Меняй зубную щетку каждые 3 месяца.",
    "🔹 Не забывай про язык — на нём скапливаются бактерии.",
    "🔹 Используй зубную нить или ирригатор каждый вечер.",
    "🔹 Не дави слишком сильно — это портит эмаль.",
    "🔹 Регулярно посещай стоматолога, даже если всё в порядке."
]

# 📁 Загрузка и сохранение

def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ⚖️ Хранилище
users = load_json(USERS_FILE)
stats = load_json(STATS_FILE)

# 🌐 Локализация
LANG = {
    "ru": {
        "start": "👋 Привет! Я помогу напоминать чистить зубы!",
        "choose_day": "📄 Выбери день недели для настройки:",
        "set_morning": "🌞 Укажи время для **утра** в формате HH:MM",
        "set_evening": "🌙 Укажи время для **вечера** в формате HH:MM",
        "confirm": "✅ Установлено на {day}:\n🌞 Утро — {morning}, 🌙 Вечер — {evening}"
    }
}

# 🚀 /start
@bot.message_handler(commands=["start"])
def send_welcome(message):
    cid = str(message.chat.id)
    if cid not in users:
        users[cid] = {}
        save_json(USERS_FILE, users)
    text = LANG["ru"]["start"] + "\n\n" + "Команды:\n" \
        • "/plan — расписание"\n" \
        • "/tip — совет"\n" \
        • "/stats — статистика"\n" \
        • "/motivate — мем"
    bot.send_message(message.chat.id, text)

# ⚖️ Расписание: установка времени
@bot.message_handler(commands=["plan"])
def ask_day(message):
    markup = types.InlineKeyboardMarkup()
    for day in DAYS:
        markup.add(types.InlineKeyboardButton(text=day, callback_data=f"set_day:{day}"))
    bot.send_message(message.chat.id, LANG["ru"]["choose_day"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_day"))
def ask_morning(call):
    cid = str(call.message.chat.id)
    day = call.data.split(":")[1]
    users.setdefault(cid, {})
    users[cid]["current_day"] = day
    save_json(USERS_FILE, users)
    bot.send_message(call.message.chat.id, LANG["ru"]["set_morning"])

@bot.message_handler(func=lambda msg: msg.text and msg.text.count(":") == 1)
def handle_morning(message):
    cid = str(message.chat.id)
    user_data = users.get(cid, {})
    if "current_day" not in user_data or "morning" in user_data.get(user_data["current_day"], {}):
        return
    day = user_data["current_day"]
    users[cid].setdefault(day, {})["morning"] = message.text.strip()
    save_json(USERS_FILE, users)
    bot.send_message(message.chat.id, LANG["ru"]["set_evening"])

@bot.message_handler(func=lambda msg: msg.text and msg.text.count(":") == 1)
def handle_evening(message):
    cid = str(message.chat.id)
    day = users[cid].get("current_day")
    users[cid][day]["evening"] = message.text.strip()
    save_json(USERS_FILE, users)
    morning = users[cid][day]["morning"]
    evening = users[cid][day]["evening"]
    bot.send_message(cid, LANG["ru"]["confirm"].format(day=day, morning=morning, evening=evening))

# ⏳ Напоминания

def scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")
        weekday = DAYS[datetime.today().weekday()]
        for cid, schedule in users.items():
            times = schedule.get(weekday, {})
            if now == times.get("morning"):
                bot.send_message(cid, "🌞 Доброе утро! Пора чистить зубы!", reply_markup=brushed_markup())
            if now == times.get("evening"):
                bot.send_message(cid, "🌙 Вечерняя чистка зовёт!", reply_markup=brushed_markup())
        threading.Event().wait(60)

# ✅ Статистика

def brushed_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(text="✅ Почистил!", callback_data="brushed"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "brushed")
def handle_brushed(call):
    cid = str(call.message.chat.id)
    today = datetime.today().strftime("%Y-%m-%d")
    stats.setdefault(cid, {}).setdefault(today, 0)
    stats[cid][today] += 1
    save_json(STATS_FILE, stats)
    bot.send_message(cid, "Записал — зубы почищены!")

@bot.message_handler(commands=["stats"])
def show_stats(message):
    cid = str(message.chat.id)
    user_stats = stats.get(cid, {})
    total = sum(user_stats.values())
    reply = f"📊 Дней с чисткой: {total}\n" + "\n".join(f"{k}: {v}" for k, v in sorted(user_stats.items()))
    bot.send_message(cid, reply)

# 🔹 Совет
@bot.message_handler(commands=["tip"])
def send_tip(message):
    bot.send_message(message.chat.id, random.choice(TIPS))

# 🚀 Мемная мотивация
@bot.message_handler(commands=["motivate"])
def send_meme(message):
    bot.send_message(message.chat.id, "🚀 Ты справишься! Даже зубы блестят от твоей решимости!")

# ⏱ Запуск
threading.Thread(target=scheduler, daemon=True).start()
bot.polling(non_stop=True)

