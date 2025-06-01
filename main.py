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

# Советы стоматолога
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

# День недели на русском
days_ru = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье"
}

# Команды
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🦷 Привет! Я — DentalCoachBot.\n\n"
        "Я помогу тебе не забывать чистить зубы утром и вечером,\n"
        "а ещё расскажу полезные советы по уходу за ртом.\n\n"
        "Команды:\n"
        "/plan — расписание чистки\n"
        "/tip — совет стоматолога\n"
        "/stats — статистика за 7 дней\n"
        "/start — это сообщение"
    )

@bot.message_handler(commands=['plan'])
def plan(message):
    bot.send_message(
        message.chat.id,
        "📅 Расписание чистки зубов:\n"
        "🕢 Утром: 07:30\n"
        "🌙 Вечером: 22:30\n"
        "⏰ Я напомню!"
    )

@bot.message_handler(commands=['tip'])
def send_tip(message):
    tip = random.choice(tips)
    bot.send_message(message.chat.id, f"🦷 Совет стоматолога:\n{tip}")

@bot.message_handler(commands=['stats'])
def show_stats(message):
    filename = "stats.json"
    chat_id = str(message.chat.id)

    if not os.path.exists(filename):
        bot.send_message(message.chat.id, "Пока нет статистики. Почисти зубы 😉")
        return

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_stats = data.get(chat_id, {})
    now = datetime.now()
    last_7_days = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

    msg = "🧾 Статистика за 7 дней:\n"
    total = 0
    for day in last_7_days:
        count = user_stats.get(day, 0)
        pretty_date = datetime.strptime(day, "%Y-%m-%d").strftime("%d.%m (%a)")
        msg += f"{pretty_date}: {count} 🪥\n"
        total += count

    msg += f"\n🔁 Всего чисток за неделю: {total}"
    bot.send_message(message.chat.id, msg)

# Запись статистики
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

    if today in data[chat_id]:
        data[chat_id][today] += 1
    else:
        data[chat_id][today] = 1

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Обработка кнопки "Почистил"
@bot.callback_query_handler(func=lambda call: call.data == "brushed")
def handle_brushed(call):
    bot.answer_callback_query(call.id, "Молодец! Так держать 🦷")
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
    bot.send_message(call.message.chat.id, "Записал — зубы почищены!")
    record_stat(call.message.chat.id)

# Напоминания по расписанию
def scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")
        if now == "07:30" or now == "22:30":
            send_reminder()
            time.sleep(60)
        time.sleep(5)

def send_reminder():
    chat_ids = [ТВОЙ_CHAT_ID_СЮДА]
    now = datetime.now()
    weekday = days_ru[now.strftime("%A")]
    date_today = now.strftime("%d.%m.%Y")
    time_label = "🕢 Утро" if now.hour < 12 else "🌙 Вечер"

    for chat_id in chat_ids:
        tip = random.choice(tips)
        msg = (
            f"{time_label} — пора чистить зубы!\n\n"
            f"📅 Сегодня {weekday}, {date_today}.\n"
            f"💡 {tip}"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Почистил!", callback_data="brushed"))
        bot.send_message(chat_id, msg, reply_markup=markup)

# Запуск
threading.Thread(target=scheduler, daemon=True).start()
bot.polling()
