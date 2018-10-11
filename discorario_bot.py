import os
from datetime import datetime
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
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
- /preference : salva un orario preferito.\n\n\
- Per consolutare il tuo orario preferito puoi scrivere solo 'orario'.\n\n\
- Puoi cercare un orario di un corso specifico. Ad esempio: \
orario informatica triennale 1 mz\n\n\
- /help : per visualizzare questo messaggio"


PREF_DEPARTMENT, PREF_COURSE, PREF_YEAR, PREF_PARTITIONING = range(4)


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


def begin_preference(bot, update, user_data):
    user_data['preference'] = {}
    courses = do.get_all_courses()
    reply_keyboard = [[course_name] for course_id, course_name in courses]
    update.message.reply_text(
        "Scegli il corso di laurea. Per annullare usa /cancel",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return PREF_COURSE


def department(bot, update, user_data):
    raise NotImplementedError


def course(bot, update, user_data):
    course_name = update.message.text.lower()
    user_data['preference']['course_name'] = course_name
    if course_name.find("magistrale") >= 0:
        reply_keyboard = [["1", "2"]]
    else:
        reply_keyboard = [["1", "2", "3"]]

    update.message.reply_text(
        "Scegli l'anno",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return PREF_YEAR


def year(bot, update, user_data):
    try:
        year = int(update.message.text)
        user_data['preference']['year'] = year
    except ValueError:
        update.message.reply_text("Anno non valido")
        return ConversationHandler.END

    reply_keyboard = [["Nessuno"], ["A-L"], ["M-Z"]]

    update.message.reply_text(
        "Scegli il partizionamento",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return PREF_PARTITIONING


def partitioning(bot, update, user_data):
    chat_id = update.message.chat_id
    partitioning = text = update.message.text

    print("partitioning:", partitioning)
    if partitioning == "Nessuno":
        user_data['preference']['partitioning'] = ''
    else:
        user_data['preference']['partitioning'] = partitioning

    preference = user_data['preference']
    print("User data:", user_data)
    try:
        print("Saving..")
        result = do.save_preference(user_id=chat_id, **preference)
        print("Saved. Result:", result)
        if result:
            update.message.reply_text("Salvato!")
            logger.log(chat_id, text, "Salvato!")
        else:
            update.message.reply_text(ERROR_MESSAGE)
            logger.log(chat_id, text, ERROR_MESSAGE, "Failed so save preference")
    except Exception as e:
        update.message.reply_text(ERROR_MESSAGE)
        logger.log(chat_id, text, ERROR_MESSAGE, f"Exception: {e}")


    return ConversationHandler.END


def cancel(bot, update, user_data):
    try:
        user_data['preference'] = {}
    except Exception:
        pass

    update.message.reply_text(
        "Salvataggio corso annullato",
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    updater = Updater(TOKEN)


    DEPARTMENT, COURSE, YEAR, PARTITIONING = range(4)
    preference_conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("preference", begin_preference, pass_user_data=True)],
        states = {
            PREF_DEPARTMENT: [MessageHandler(Filters.text, department, pass_user_data=True)],
            PREF_COURSE: [MessageHandler(Filters.text, course, pass_user_data=True)],
            PREF_YEAR: [MessageHandler(Filters.text, year, pass_user_data=True)],
            PREF_PARTITIONING: [MessageHandler(Filters.text, partitioning, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)]
    )

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(preference_conversation_handler)
    dp.add_handler(MessageHandler(Filters.text, discorario))



    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
