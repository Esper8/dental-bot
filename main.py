
import telebot
import threading
import time
import random
from telebot import types
from datetime import datetime, timedelta
import json
import os

TOKEN = "8187925078:AAFHnjRxLuqajMkZ_06mwgyFiqED8pHEDCY"
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

tips = [
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

days_ru = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье"
}

language = {"ru": "Русский", "en": "English"}
user_lang = {}

def get_lang(chat_id):
    return user_lang.get(str(chat_id), "ru")

def translate(msg_ru, msg_en, chat_id):
    return msg_ru if get_lang(chat_id) == "ru" else msg_en

@bot.message_handler(commands=['start'])
def start(message):
    cid = str(message.chat.id)
    save_user(cid)
    bot.send_message(
        message.chat.id,
        translate(
            "🦷 Привет! Я — DentalCoachBot.\n\nКоманды:\n/plan — расписание\n/tip — совет\n/stats — статистика\n/lang — язык\n/motivate — мем",
            "🦷 Hello! I'm DentalCoachBot.\n\nCommands:\n/plan — routine\n/tip — tip\n/stats — stats\n/lang — language\n/motivate — meme",
            cid
        )
    )

@bot.message_handler(commands=['plan'])
def plan(message):
    bot.send_message(message.chat.id, translate(
        "📅 Утром: 07:30\n🌙 Вечером: 22:30",
        "📅 Morning: 07:30\n🌙 Evening: 22:30",
        message.chat.id
    ))

@bot.message_handler(commands=['tip'])
def send_tip(message):
    tip = random.choice(tips)
    bot.send_message(message.chat.id, f"🦷 {translate('Совет стоматолога:', 'Dental tip:', message.chat.id)}\n{tip}")

@bot.message_handler(commands=['lang'])
def lang(message):
    cid = str(message.chat.id)
    current = get_lang(cid)
    new_lang = "en" if current == "ru" else "ru"
    user_lang[cid] = new_lang
    save_langs()
    bot.send_message(message.chat.id, f"🌍 {translate('Язык переключен на:', 'Language switched to: ', message.chat.id)} {language[new_lang]}")

@bot.message_handler(commands=['motivate'])
def motivate(message):
    meme_folder = "memes"
    files = [f for f in os.listdir(meme_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if files:
        img_path = os.path.join(meme_folder, random.choice(files))
        with open(img_path, 'rb') as photo:
            bot.send_photo(message.chat.id, photo)
    else:
        bot.send_message(message.chat.id, translate("Нет мемов 😢", "No memes 😢", message.chat.id))

@bot.message_handler(commands=['stats'])
def show_stats(message):
    filename = "stats.json"
    cid = str(message.chat.id)
    if not os.path.exists(filename):
        bot.send_message(message.chat.id, translate("Пока нет статистики.", "No stats yet.", message.chat.id))
        return
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    user_stats = data.get(cid, {})
    now = datetime.now()
    last_7_days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    msg = "📊\n"
    total = 0
    for day in last_7_days:
        count = user_stats.get(day, 0)
        pretty_date = datetime.strptime(day, "%Y-%m-%d").strftime("%d.%m (%a)")
        msg += f"{pretty_date}: {count} 🪥\n"
        total += count
    msg += f"🔥 {translate('Всего:', 'Total:', message.chat.id)} {total}"
    bot.send_message(message.chat.id, msg)

def record_stat(chat_id):
    today = datetime.now().strftime("%Y-%m-%d")
    filename = "stats.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}
    chat_id = str(chat_id)
    if chat_id not in data:
        data[chat_id] = {}
    data[chat_id][today] = data[chat_id].get(today, 0) + 1
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@bot.callback_query_handler(func=lambda call: call.data == "brushed")
def handle_brushed(call):
    bot.answer_callback_query(call.id, "Молодец! Так держать 🦷")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id, "Записал — зубы почищены!")
    record_stat(call.message.chat.id)

def send_reminder():
    users = load_users()
    now = datetime.now()
    weekday = days_ru[now.strftime("%A")]
    date_today = now.strftime("%d.%m.%Y")
    time_label = "🕢 Утро" if now.hour < 12 else "🌙 Вечер"
    for chat_id in users:
        tip = random.choice(tips)
        msg = f"{time_label} — {translate('пора чистить зубы!', 'time to brush!', chat_id)}\n\n📅 {weekday}, {date_today}.\n💡 {tip}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Почистил!", callback_data="brushed"))
        bot.send_message(chat_id, msg, reply_markup=markup)

def weekly_report():
    users = load_users()
    for uid in users:
        dummy = types.SimpleNamespace()
        dummy.chat = types.SimpleNamespace()
        dummy.chat.id = uid
        show_stats(dummy)

def scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")
        if now == "07:30" or now == "22:30":
            send_reminder()
            time.sleep(60)
        elif now == "20:00" and datetime.now().weekday() == 6:
            weekly_report()
            time.sleep(60)
        time.sleep(5)

def save_user(cid):
    filename = "users.json"
    cid = str(cid)
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []
    if cid not in data:
        data.append(cid)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f)

def load_users():
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_langs():
    with open("langs.json", "w", encoding="utf-8") as f:
        json.dump(user_lang, f)

threading.Thread(target=scheduler, daemon=True).start()
bot.polling()
