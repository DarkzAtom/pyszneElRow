import json
import time
from telegram import Bot, Update
from telegram.ext import Updater, CommandHandler, CallbackContext


TOKEN = 'tempdeleted'

CHAT_ID_FILE = 'chat_ids.json'

bot = Bot(token=TOKEN)

def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    chat_ids = load_chat_ids()
    if chat_id not in chat_ids:
        chat_ids.append(chat_id)
        save_chat_ids(chat_ids)
    update.message.reply_text("You will receive notifications when the script finishes.")

def load_chat_ids():
    try:
        with open(CHAT_ID_FILE, 'r') as file:
            chat_ids = json.load(file)
    except FileNotFoundError:
        chat_ids = []
    return chat_ids

def save_chat_ids(chat_ids):
    with open(CHAT_ID_FILE, 'w') as file:
        json.dump(chat_ids, file)

def send_telegram_message(message):
    chat_ids = load_chat_ids()
    for chat_id in chat_ids:
        bot.send_message(chat_id=chat_id, text=message)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))

    updater.start_polling()

    send_telegram_message("В Познани появилась вакансия на курьера в Пышне на электроровере! Вперед, гойда!")

    updater.stop()


if __name__ == '__main__':
    main()
