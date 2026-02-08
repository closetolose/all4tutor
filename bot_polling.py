import telebot
import os

TOKEN = "8505922369:AAHAv595sVcvPL5dRwuOcBhP_R_kW2jFgJk"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    text = (
        f"👋 Привет! Я бот All4Tutors.\n\n"
        f"Твой Telegram ID: <code>{user_id}</code>\n\n"
        f"Скопируй это число и вставь его в поле 'Telegram ID' в своем профиле на сайте, "
        f"чтобы получать уведомления о занятиях и ДЗ."
    )
    bot.reply_to(message, text, parse_mode='HTML')

if __name__ == "__main__":
    print("Бот запущен...")
    bot.polling(none_stop=True)