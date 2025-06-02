
@bot.message_handler(commands=["plan"])
def show_plan(message):
    cid = str(message.chat.id)
    users = load_users()
    user_data = users.get(cid, {})
    plan = "План на неделю:\n"
    for day in DAYS:
        times = user_data.get(day, {})
        plan += f"{day}: 🌞 {times.get('morning', '-')} / 🌛 {times.get('evening', '-')}\n"
    bot.send_message(cid, plan)

@bot.message_handler(commands=["tip"])
def send_tip(message):
    bot.send_message(message.chat.id, random.choice(TIPS))

@bot.message_handler(commands=["motivate"])
def send_meme(message):
    bot.send_message(message.chat.id, "🚀 Ты справился! Даже зубы блестят от твоей решимости!")

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
                bot.send_message(cid, "🌛 Вечерняя чистка зовёт!")
        threading.Event().wait(60)

threading.Thread(target=scheduler, daemon=True).start()
bot.polling(non_stop=True)
