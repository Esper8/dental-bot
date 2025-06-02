import telebot
import json
import threading
from datetime import datetime
from telebot import types

bot = telebot.TeleBot("YOUR_BOT_TOKEN")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TIPS = [
    "Меняй зубную щётку каждые 3 месяца.",
    "Чисти зубы не менее 2 минут.",
    "Не забывай про язык — на нём скапливаются бактерии.",
    "Полощи рот после еды, если не можешь сразу почистить зубы.",
    "Используй зубную нить или ирригатор каждый вечер.",
    "Не надави слишком сильно — это портит эмаль.",
    "Избегай сладостей перед сном, если не планируешь чистить зубы.",
    "Регулярно посещай стоматолога, даже если всё в порядке.",
    "Не забывай про чистку задних зубов — они страдают чаще всего.",
    "Полезно заканчивать чистку ополаскивателем без спирта."
]

def load_users():
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    cid = str(message.chat.id)
    users = load_users()
    if cid not in users:
        users[cid] = {}
        save_users(users)
    text = "👋 Привет! Я помогу напоминать чистить зубы!

Команды:
/plan — расписание
/tip — совет
/stats — статистика
/lang — язык
/motivate — мем"
    bot.send_message(cid, text)
    ask_day(cid)

def ask_day(cid):
    markup = types.InlineKeyboardMarkup()
    for day in DAYS:
        markup.add(types.InlineKeyboardButton(day, callback_data=f"set_day:{day}"))
    bot.send_message(cid, "📅 Выбери день недели для настройки:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("set_day:"))
def get_day(call):
    cid = str(call.message.chat.id)
    day = call.data.split(":")[1]
    bot.send_message(cid, f"🕰 Укажи время для **утра** в формате HH:MM")
    bot.register_next_step_handler(call.message, get_morning_time, cid, day)

def get_morning_time(message, cid, day):
    morning = message.text.strip()
    bot.send_message(cid, f"🌙 Укажи время для **вечера** в формате HH:MM")
    bot.register_next_step_handler(message, get_evening_time, cid, day, morning)

def get_evening_time(message, cid, day, morning):
    evening = message.text.strip()
    users = load_users()
    if cid not in users:
        users[cid] = {}
    users[cid][day] = {"morning": morning, "evening": evening}
    save_users(users)
    bot.send_message(cid, f"✅ Установлено на {day}:
🌞Утро — {morning}, 🌙Вечер — {evening}")
    ask_day(cid)

@bot.message_handler(commands=["plan"])
def show_plan(message):
    cid = str(message.chat.id)
    users = load_users()
    user_data = users.get(cid, {})
    plan = "📆 План на неделю:
"
    for day in DAYS:
        times = user_data.get(day, {})
        plan += f"{day}: 🌞{times.get('morning', '-')} / 🌙{times.get('evening', '-')}
"
    bot.send_message(cid, plan)

@bot.message_handler(commands=["tip"])
def send_tip(message):
    bot.send_message(message.chat.id, random.choice(TIPS))

@bot.message_handler(commands=["motivate"])
def send_meme(message):
    bot.send_message(message.chat.id, "🎯 Ты справишься! Даже зубы блестят от твоей решимости!")

def scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")
        weekday = DAYS[datetime.today().weekday()]
        users = load_users()
        for cid, schedule in users.items():
            times = schedule.get(weekday, {})
            if now == times.get("morning"):
                bot.send_message(cid, "🌞 Доброе утро! Пора чистить зубы!")
            if now == times.get("evening"):
                bot.send_message(cid, "🌙 Вечерняя чистка зовёт!")
        threading.Event().wait(60)

threading.Thread(target=scheduler, daemon=True).start()
bot.polling(none_stop=True)