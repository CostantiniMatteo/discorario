import os
from datetime import datetime
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import discorario as do
import logger


TOKEN = os.environ["TELEGRAM_TOKEN"]
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)

ERROR_MESSAGE = "Qualcosa è andato storto. Controlla di non \
aver fatto errori. Devi inserire il nome del corso, l'anno ed eventualmente il gruppo (AL/MZ). \
Esempio: /preference informatica triennale 2 MZ\n\
Se il problema persiste segnala l'errore!"

NO_PREFERENCE_MESSAGE = "Pare tu non abbia nessun orario\
preferito. Puoi salvarne uno con il comando /preference"

HELP_MESSAGE = "Ecco le funzioni:\n\n\
- /preference : salva un orario preferito.\n\
/preference nome corso anno [gruppo].\n\
Ad esempio: /preference informatica triennale 2 al\n\n\
- Per consolutare il tuo orario preferito puoi scrivere solo 'orario'.\n\n\
- Puoi cercare un orario di un corso specifico. Ad esempio: \
orario informatica triennale 1 mz\n\n\
- /help : per visualizzare questo messaggio"


def discorario(bot, update):
    try:
        chat_id = update.message.chat_id
        query = update.message.text.lower().strip()
        today = datetime.now().strftime('%d-%m-%Y')

        if query.find("orario") < 0:
            preference = do.get_user_preference(chat_id)

            if not preference:
                update.message.reply_text(NO_PREFERENCE_MESSAGE)
                logger.log(chat_id, query, NO_PREFERENCE_MESSAGE)
                return

            schedule = do.get_schedule(**preference, date=today)
            response = do.get_next_lecture(query, schedule)
            update.message.reply_text(response)
            logger.log(chat_id, query, response)
            return

        if query == "orario":
            preference = do.get_user_preference(chat_id)
            if not preference:
                update.message.reply_text(NO_PREFERENCE_MESSAGE)
                logger.log(chat_id, query, NO_PREFERENCE_MESSAGE)
                return
            schedule = do.get_schedule(**preference, date=today)
        else:
            params = parse_query(query)
            schedule = do.get_schedule(date=today, **params)

        send_schedule(bot, update, schedule)
        logger.log(chat_id, query, "*Sent document*")

    except Exception as e:
        update.message.reply_text("Qualcosa è andato storto.")
        logger.log(chat_id, query, "Qualcosa è andato storto.", f"Exception: {e}")


def send_schedule(bot, update, schedule):
    outfile = "schedule"
    format = "pdf"
    do.save_schedule(schedule, outfile, format=format)
    with open(f"/home/matteo_angelo_costantini/discorario/{outfile}.{format}", "rb") as f:
        bot.send_document(chat_id=update.message.chat_id, document=f, timeout=10000)


def start(bot, update):
    help(bot, update)


def help(bot, update):
    update.message.reply_text(HELP_MESSAGE)
    logger.log(update.message.chat_id, update.message.text, HELP_MESSAGE)


def save_preference(bot, update):
    try:
        chat_id = update.message.chat_id
        text = update.message.text.lower().strip()

        if text == "/preference":
            update.message.reply_text(ERROR_MESSAGE)
            logger.log(chat_id, text, ERROR_MESSAGE, "/preference only")
            return

        preference = parse_query(text)
        result = do.save_preference(user_id=chat_id, **preference)
        if result:
            update.message.reply_text("Salvato!")
            logger.log(chat_id, text, "Salvato!")
        else:
            update.message.reply_text(ERROR_MESSAGE)
            logger.log(chat_id, text, ERROR_MESSAGE, "Failed so save preference")
    except Exception as e:
        update.message.reply_text(ERROR_MESSAGE)
        logger.log(chat_id, text, ERROR_MESSAGE, f"Exception: {e}")


def parse_query(text):
    s = text.lower().split()

    if len(s) == 1:
        return {
            'course_name': 'informatica magistrale',
            'partitioning': '',
            'year': 2
        }

    res = {}
    if s[-1].find('-') > 0 or len(s[-1]) == 2:
        res['partitioning'] = s[-1]
        res['year'] = int(s[-2])
        res['course_name'] = ' '.join(s[1:-2])
    else:
        res['partitioning'] = ''
        res['year'] = s[-1]
        res['course_name'] = ' '.join(s[1:-1])

    return res


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("preference", save_preference))
    dp.add_handler(MessageHandler(Filters.text, discorario))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
