import os, json
from datetime import datetime
from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackQueryHandler,
)
from configuration import TOKEN, BASE_PATH
from time_utils import days
import discorario as do
import logger


BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)

ERROR_MESSAGE = "Qualcosa è andato storto."

NO_PREFERENCE_MESSAGE = "Pare tu non abbia nessun orario\
preferito. Puoi salvarne uno con il comando /preference"

HELP_MESSAGE = "Ecco le funzioni:\n\n\
- /preference : salva un orario preferito.\n\n\
- Per consolutare il tuo orario preferito puoi scrivere solo 'orario' \
o usare il comando /orario.\n\n\
- Puoi cercare un orario di un corso specifico. Ad esempio: \
orario informatica triennale 1 mz\n\n\
- /help : per visualizzare questo messaggio"


PREF_DEPARTMENT, PREF_COURSE, PREF_YEAR, PREF_PARTITIONING = range(4)


def discorario(bot, update):
    try:
        if query.find("orario") < 0:
            find_next_lecture(bot, update)

        if query == "orario":
            send_schedule(bot, update)

    except Exception as e:
        update.message.reply_text(ERROR_MESSAGE)
        logger.log(chat_id, query, ERROR_MESSAGE, f"Exception: {e}")


def send_schedule(bot, update):
    chat_id = update.message.chat_id
    query = update.message.text

    date = datetime.now()

    try:
        schedule = do.get_weekly_schedule(chat_id, date=date)
    except KeyError:
        update.message.reply_text(NO_PREFERENCE_MESSAGE)
        logger.log(chat_id, query, NO_PREFERENCE_MESSAGE)
    else:
        # TODO: Check if there are other lectures for the current week
        # if not, get next week's schedule

        outfile = "schedule"
        format = "pdf"
        # TODO: Needs to be updated
        do.save_schedule(schedule, outfile, format=format)
        with open(os.path.join(BASE_PATH, f"{outfile}.{format}"), "rb") as f:
            bot.send_document(
                chat_id=update.message.chat_id, document=f, timeout=10000
            )

        logger.log(chat_id, query, "*Sent document*")


def find_next_lecture(bot, update):
    chat_id = update.message.chat_id
    query = update.message.text.lower().strip()
    date = datetime.now()

    try:
        lecture = do.get_next_lecture(chat_id, date, query)
    except KeyError:
        update.message.reply_text(NO_PREFERENCE_MESSAGE)
        logger.log(chat_id, query, NO_PREFERENCE_MESSAGE)
    else:
        if not lecture:
            update.message.reply_text("¯\\_(ツ)_/¯")
        else:
            weekday = days[lecture.begin.weekday()]
            hours = lecture.begin.strftime("%H:%M")
            response = f"La prossima lezione di {lecture.course} è {weekday} alle {hours} in aula {lecture.room}."
            update.message.reply_text(response)

            logger.log(chat_id, query, response)


def start(bot, update):
    help(bot, update)


def help(bot, update):
    update.message.reply_text(HELP_MESSAGE)
    logger.log(update.message.chat_id, update.message.text, HELP_MESSAGE)


def begin_preference(bot, update, user_data):
    user_data["preference"] = {}
    departments = do.get_all_departments()
    reply_keyboard = [
        [InlineKeyboardButton(dep.replace("_", " "), callback_data=dep)]
        for dep in departments
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    update.message.reply_text(
        "Scegli il dipartimento. Per annullare, in qualsiasi momento, usa /cancel",
        reply_markup=reply_markup,
    )

    return PREF_DEPARTMENT


def department(bot, update, user_data):
    department = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id

    user_data["preference"]["department"] = department

    courses = do.get_all_degree_courses()
    reply_keyboard = [
        [InlineKeyboardButton(course.name, callback_data=course.code)]
        for course in courses
        if course.department == user_data["preference"]["department"]
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    update.callback_query.message.reply_text(
        "Scegli il corso di laurea.", reply_markup=reply_markup
    )
    return PREF_COURSE


def course(bot, update, user_data):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id

    course_code = update.callback_query.data.lower()
    courses = do.get_all_degree_courses()
    course = next(c for c in courses if c.code.lower() == course_code.lower())

    user_data["preference"]["course_name"] = course.name
    user_data["preference"]["course_id"] = course.code

    reply_keyboard = [
        [InlineKeyboardButton(year["name"], callback_data=year["code"])]
        for year in course.years
    ]
    update.callback_query.message.reply_text(
        text="Scegli l'anno", reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return PREF_YEAR


def year(bot, update, user_data):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    text = update.callback_query.message.text

    year = update.callback_query.data
    user_data["preference"]["year"] = year
    preference = user_data["preference"]
    try:
        result = do.save_preference(
            user_id=str(chat_id), **user_data["preference"]
        )
        if result:
            update.callback_query.message.reply_text(text="Salvato")
            logger.log(chat_id, text, "Salvato!")
        else:
            update.callback_query.message.reply_text(text=ERROR_MESSAGE)
            logger.log(
                chat_id, text, ERROR_MESSAGE, "Failed so save preference"
            )
    except Exception as e:
        update.callback_query.message.reply_text(text=ERROR_MESSAGE)
        logger.log(chat_id, text, ERROR_MESSAGE, f"Exception: {e}")

    return ConversationHandler.END


# TODO: Custom calendar


def cancel(bot, update, user_data):
    try:
        user_data["preference"] = {}
    except Exception:
        pass

    update.message.reply_text("Salvataggio corso annullato")

    return ConversationHandler.END


def main():
    updater = Updater(TOKEN)

    DEPARTMENT, COURSE, YEAR, PARTITIONING = range(4)
    preference_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("preference", begin_preference, pass_user_data=True)
        ],
        states={
            PREF_DEPARTMENT: [
                CallbackQueryHandler(department, pass_user_data=True)
            ],
            PREF_COURSE: [CallbackQueryHandler(course, pass_user_data=True)],
            PREF_YEAR: [CallbackQueryHandler(year, pass_user_data=True)],
        },
        fallbacks=[CommandHandler("cancel", cancel, pass_user_data=True)],
    )

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("orario", send_schedule))
    dp.add_handler(preference_conversation_handler)
    dp.add_handler(MessageHandler(Filters.text, discorario))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
