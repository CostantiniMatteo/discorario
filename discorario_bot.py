#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, logging
from datetime import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from discorario import *

TOKEN = os.environ["TELEGRAM_TOKEN"]
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def discorario(bot, update):
    try:
        chat_id = update.message.chat_id
        query = update.message.text.lower()

        if update.message.text.find("orario") >= 0:
            schedule = get_schedule(date="01-10-2018")
            save_schedule(schedule, "schedule.png")
            with open("schedule.png", "rb") as f:
                bot.send_document(chat_id=chat_id, document=f, timeout=10000)
        else:
            try:
                response = get_next_lecture(query)
            except Exception as e:
                response = "¯\\_(ツ)_/¯"
            update.message.reply_text(response)

    except Exception as e:
        error(bot, update, str(e))


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def start(bot, update):
    help(bot, update)


def help(bot, update):
    update.message.reply_text(
        "Cerca un corso o scrivi 'orario' per ricevere l'orario settimanale"
    )


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text, discorario))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
