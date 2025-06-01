
import telebot
import schedule
import time
import threading
import random
from datetime import datetime

TOKEN = "8187925078:AAFxC8nDvloidqMf-DNgd7Dt2yvRbZdvou4"
bot = telebot.TeleBot(TOKEN)

chat_id = None

schedule_plan = {
    "Monday": ("R.O.C.S.", "Elmex"),
    "Tuesday": ("R.O.C.S.", "Elmex"),
    "Wednesday": ("Opalescence", "Elmex"),
    "Thursday": ("R.O.C.S.", "Elmex"),
    "Friday": ("R.O.C.S.", "Opalescence"),
    "Saturday": ("R.O.C.S.", "Elmex"),
    "Sunday": ("R.O.C.S.", "Elmex")
}

tips = [
    "💡 Не пей кофе или чай в течение 30 минут после чистки зубов.",
    "🪥 Меняй щётку каждые 2–3 месяца.",
    "🦷 Вечерняя чистка особенно важна.",
    "😬 Не нажимай сильно щёткой — эмаль стирается.",
    "🧊 Холодная вода может усиливать чувствительность.",
    "🧼 Используй зубную нить хотя бы через день."
]

@bot.message_handler(commands=["start"])
def send_welcome(message):
    global chat_id
    chat_id = message.chat.id
    bot.send_message(chat_id, "🦷 Привет, я DentalCoachBot! Напоминаю про чистку зубов 🪥")

@bot.message_handler(commands=["today"])
def today_plan(message):
    today = datetime.today().strftime("%A")
    morning, evening = schedule_plan[today]
    bot.send_message(message.chat.id, f"📅 Сегодня: утром — {morning}, вечером — {evening}")

@bot.message_handler(commands=["plan"])
def full_plan(message):
    text = "🗓 План на неделю:\n"
"
    for day, (morning, evening) in schedule_plan.items():
        text += f"{day}: 🌞 {morning} / 🌙 {evening}
"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=["tip"])
def send_tip(message):
    bot.send_message(message.chat.id, random.choice(tips))

def morning_reminder():
    if chat_id:
        today = datetime.today().strftime("%A")
        morning = schedule_plan[today][0]
        bot.send_message(chat_id, f"🌞 Утро! Сегодня чистим зубы с {morning}")

def evening_reminder():
    if chat_id:
        today = datetime.today().strftime("%A")
        evening = schedule_plan[today][1]
        bot.send_message(chat_id, f"🌙 Вечер! Используй {evening}")

def schedule_loop():
    schedule.every().day.at("07:30").do(morning_reminder)
    schedule.every().day.at("22:30").do(evening_reminder)
    while True:
        schedule.run_pending()
        time.sleep(1)

threading.Thread(target=schedule_loop).start()
bot.polling()
