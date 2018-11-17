import os, json
from datetime import datetime, timedelta
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
    RegexHandler,
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
- /cdl : salva un orario preferito.\n\n\
- /calendario : scegli i corsi da visualizzare\n\n\
- Per consolutare il tuo orario preferito puoi scrivere solo 'orario' \
o usare il comando /orario.\n\n\
- /help : per visualizzare questo messaggio"

PREF_DEPARTMENT, PREF_COURSE, PREF_YEAR = range(3)
UPDATE_AGENDA = 0


def send_schedule(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    query = update.message.text

    date = datetime.now()

    try:
        schedule = do.get_weekly_schedule(chat_id, date=date)
    except KeyError:
        update.message.reply_text(NO_PREFERENCE_MESSAGE)
        logger.log(user, query, NO_PREFERENCE_MESSAGE)
    else:
        next_lecture = schedule.get_next_lecture(query="", date=date)

        if next_lecture is None:
            date = date + timedelta(days=7)
            schedule = do.get_weekly_schedule(chat_id, date=date)

        outfile = "schedule"
        format = "pdf"
        filename = do.write_schedule(schedule, format=format)
        fullpath = os.path.join(BASE_PATH, filename)
        with open(fullpath, "rb") as f:
            bot.send_document(
                chat_id=update.message.chat_id,
                document=f,
                filename=f"schedule.{format}",
                timeout=10000,
            )
        os.remove(fullpath)
        logger.log(user, query, "*Sent document*")


def find_next_lecture(bot, update):
    user = update.message.from_user
    chat_id = update.message.chat_id
    query = update.message.text.lower().strip()
    date = datetime.now()

    try:
        lecture = do.get_next_lecture(chat_id, date, query)
    except KeyError:
        update.message.reply_text(NO_PREFERENCE_MESSAGE)
        logger.log(user, query, NO_PREFERENCE_MESSAGE)
    else:
        if not lecture:
            update.message.reply_text("¯\\_(ツ)_/¯")
            logger.log(user, query, "¯\\_(ツ)_/¯")
        else:
            weekday = days[lecture.begin.weekday()]
            hours = lecture.begin.strftime("%H:%M")
            response = f"La prossima lezione di {lecture.course} è {weekday} alle {hours} in aula {lecture.room}."
            update.message.reply_text(response)

            logger.log(user, query, response)


def start(bot, update):
    help(bot, update)


def help(bot, update):
    update.message.reply_text(HELP_MESSAGE)
    logger.log(update.message.from_user, update.message.text, HELP_MESSAGE)


def begin_preference(bot, update, user_data):
    user = update.message.from_user
    query = update.message.text.lower().strip()
    user_data["preference"] = {}
    departments = do.get_all_departments()

    reply_keyboard = [
        [InlineKeyboardButton(dep.replace("_", " "), callback_data=dep)]
        for dep in departments
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)

    response = "Scegli il dipartimento. Per annullare, in qualsiasi momento, usa /cancel"
    update.message.reply_text(text=response, reply_markup=reply_markup)

    logger.log(user, query, response)

    return PREF_DEPARTMENT


def department(bot, update, user_data):
    user = update.callback_query.from_user
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    department = update.callback_query.data

    user_data["preference"]["department"] = department

    courses = do.get_all_degree_courses()
    reply_keyboard = [
        [InlineKeyboardButton(course.name, callback_data=course.code)]
        for course in courses
        if course.department == user_data["preference"]["department"]
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    response = "Scegli il corso di laurea."
    bot.edit_message_text(
        text=response,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=reply_markup,
    )

    logger.log(user, department, response)

    return PREF_COURSE


def course(bot, update, user_data):
    user = update.callback_query.from_user
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
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    response = "Scegli l'anno"
    bot.edit_message_text(
        text=response,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=reply_markup,
    )

    logger.log(user, f"{course.code} - {course.name}", response)

    return PREF_YEAR


def year(bot, update, user_data):
    user = update.callback_query.from_user
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
            bot.edit_message_text(
                text="Salvato! Ora scrivi 'orario' o /orario!",
                chat_id=chat_id,
                message_id=message_id,
            )
            logger.log(user, text, "Salvato! Ora scrivi 'orario' o /orario!")
        else:
            bot.edit_message_text(
                text=ERROR_MESSAGE, chat_id=chat_id, message_id=message_id
            )
            logger.log(user, text, ERROR_MESSAGE, "Failed so save preference")
    except Exception as e:
        bot.edit_message_text(
            text=ERROR_MESSAGE, chat_id=chat_id, message_id=message_id
        )
        logger.log(user, text, ERROR_MESSAGE, f"Exception: {e}")

    return ConversationHandler.END


def build_agenda_reply_keyboard(courses, user_agenda):
    reply_keyboard = [[InlineKeyboardButton("Salva", callback_data="done")]]
    reply_keyboard += [
        [InlineKeyboardButton(f"✔ {c}", callback_data=c)]
        if c in user_agenda
        else [InlineKeyboardButton(c, callback_data=c)]
        for c in courses
    ]
    reply_keyboard += [[InlineKeyboardButton("Salva", callback_data="done")]]
    return reply_keyboard


def begin_agenda(bot, update, user_data):
    user = update.message.from_user
    chat_id = update.message.chat_id
    query = update.message.text

    preference = do.get_preference(chat_id)

    if not preference:
        update.message.reply_text(NO_PREFERENCE_MESSAGE)
        logger.log(user, query, NO_PREFERENCE_MESSAGE)
        return ConversationHandler.END

    user_agenda = user_data["agenda"] = do.get_user_agenda(chat_id)
    courses = user_data["courses"] = do.get_courses(**preference)

    reply_keyboard = build_agenda_reply_keyboard(courses, user_agenda)
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    response = "Seleziona i corsi che ti interessano."
    update.message.reply_text(text=response, reply_markup=reply_markup)

    logger.log(user, query, response)

    return UPDATE_AGENDA


def update_agenda(bot, update, user_data):
    user = update.callback_query.from_user
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    course = update.callback_query.data
    courses = user_data["courses"]
    user_agenda = user_data["agenda"]

    if course == "done":
        do.save_user_agenda(chat_id, user_data["agenda"])
        bot.edit_message_text(
            text="Calendario salvato!", chat_id=chat_id, message_id=message_id
        )
        return ConversationHandler.END

    if course not in user_data["agenda"]:
        user_data["agenda"].append(course)
    else:
        user_data["agenda"].remove(course)

    reply_keyboard = build_agenda_reply_keyboard(courses, user_data["agenda"])
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    response = "Seleziona i corsi che ti interessano."
    bot.edit_message_text(
        text=response,
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=reply_markup,
    )

    logger.log(user, course, response)

    return UPDATE_AGENDA


def cancel(bot, update, user_data):
    user_data.clear()
    update.message.reply_text("Salvataggio corso annullato")
    logger.log(update.message.from_user, text, "Salvataggio corso annullato")

    return ConversationHandler.END


def main():
    updater = Updater(TOKEN)

    preference_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("cdl", begin_preference, pass_user_data=True)
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

    agenda_conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("calendario", begin_agenda, pass_user_data=True)
        ],
        states={
            UPDATE_AGENDA: [
                CallbackQueryHandler(update_agenda, pass_user_data=True)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel, pass_user_data=True)],
    )

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("orario", send_schedule))
    dp.add_handler(RegexHandler("^[^a-zA-Z]*orario[^a-zA-Z]*$", send_schedule))
    dp.add_handler(preference_conversation_handler)
    dp.add_handler(agenda_conversation_handler)
    dp.add_handler(MessageHandler(Filters.text, find_next_lecture))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
