import telebot
from telebot import types
import json
import os
import threading
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(6, 13) for m in (0, 30)] + [f"{h:02d}:{m:02d}" for h in range(18, 24) for m in (0, 30)]

TIPS = [
    "Меняй зубную щётку каждые 3 месяца.",
    "Чисти зубы не менее 2 минут.",
    "Не забывай про язык — на нём скапливаются бактерии.",
    "Полоскай рот после еды, если не можешь сразу почистить зубы.",
    "Используй зубную нить или ирригатор каждый вечер.",
    "Не надави слишком сильно — это портит эмаль.",
    "Избегай сладостей перед сном, если не планируешь чистить зубы.",
    "Регулярно посещай стоматолога, даже если всё в порядке.",
    "Не забывай про чистку задних зубов — они страдают чаще всего.",
    "Полезно заканчивать чистку ополаскивателем без спирта."
]

USERS_FILE = "users.json"


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    cid = str(message.chat.id)
    users = load_users()
    if cid not in users:
        users[cid] = {}
        save_users(users)
    bot.send_message(cid, "\ud83d\udc4b Привет! Я помогу напоминать чистить зубы!\n\nКоманды:\n/plan — расписание\n/tip — совет\n/stats — статистика\n/lang — язык\n/motivate — мем")
    ask_day(cid)


def ask_day(cid):
    markup = types.InlineKeyboardMarkup()
    for day in DAYS:
        markup.add(types.InlineKeyboardButton(text=day, callback_data=f"set_day:{day}"))
    bot.send_message(cid, "\ud83d\udcc4 Выбери день недели для настройки:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("set_day:"))
def choose_time_morning(call):
    cid = str(call.message.chat.id)
    day = call.data.split(":")[1]
    bot.answer_callback_query(call.id)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(cid, f"\ud83c\udf1e Укажи время для **утра** в формате HH:MM")
    bot.register_next_step_handler(call.message, save_time, day, "morning")


def save_time(message, day, time_type):
    cid = str(message.chat.id)
    time = message.text.strip()
    users = load_users()

    if cid not in users:
        users[cid] = {}
    if day not in users[cid]:
        users[cid][day] = {}

    users[cid][day][time_type] = time
    save_users(users)

    if time_type == "morning":
        bot.send_message(cid, f"\ud83c\udf1a Укажи время для **вечера** в формате HH:MM")
        bot.register_next_step_handler(message, save_time, day, "evening")
    else:
        morning = users[cid][day].get("morning", "—")
        evening = users[cid][day].get("evening", "—")
        bot.send_message(cid, f"✅ Установлено на {day}:\n\ud83c\udf1e Утро — {morning}, \ud83c\udf1a Вечер — {evening}")
        ask_day(cid)


@bot.message_handler(commands=["plan"])
def show_plan(message):
    cid = str(message.chat.id)
    users = load_users()
    user_data = users.get(cid, {})
    plan = "План на неделю:\n"
    for day in DAYS:
        times = user_data.get(day, {})
        plan += f"{day}: \ud83c\udf1e {times.get('morning', '—')} / \ud83c\udf1a {times.get('evening', '—')}\n"
    bot.send_message(cid, plan)


@bot.message_handler(commands=["tip"])
def send_tip(message):
    bot.send_message(message.chat.id, random.choice(TIPS))


@bot.message_handler(commands=["motivate"])
def send_meme(message):
    bot.send_message(message.chat.id, "\ud83d\ude80 Ты справишься! Даже зубы блестят от твоей решимости!")


def scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")
        weekday = DAYS[datetime.today().weekday()]
        users = load_users()
        for cid, schedule in users.items():
            times = schedule.get(weekday, {})
            if now == times.get("morning"):
                bot.send_message(cid, "\ud83c\udf1e Доброе утро! Пора чистить зубы!")
            if now == times.get("evening"):
                bot.send_message(cid, "\ud83c\udf1a Вечерняя чистка зовёт!")
        threading.Event().wait(60)


threading.Thread(target=scheduler, daemon=True).start()
bot.polling(none_stop=True)
