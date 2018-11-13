import os
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
        chat_id = update.message.chat_id
        query = update.message.text.lower().strip()
        today = datetime.now().strftime("%d-%m-%Y")

        if query.find("orario") < 0:
            find_next_lecture(update, chat_id, query, today)
            return

        if query == "orario":
            schedule = orario(update, chat_id, query, today)
        else:
            params = parse_query(query)
            schedule = do.get_schedule(date=today, **params)

        send_schedule(bot, update, schedule)
        logger.log(chat_id, query, "*Sent document*")

    except Exception as e:
        update.message.reply_text(ERROR_MESSAGE)
        logger.log(chat_id, query, ERROR_MESSAGE, f"Exception: {e}")


def orario(update, chat_id, query, today):
    preference = do.get_user_preference(chat_id)
    if not preference:
        update.message.reply_text(NO_PREFERENCE_MESSAGE)
        logger.log(chat_id, query, NO_PREFERENCE_MESSAGE)
        return
    return do.get_schedule(**preference, date=today)


def find_next_lecture(update, chat_id, query, today):
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


def send_schedule(bot, update, schedule):
    outfile = "schedule"
    format = "pdf"
    do.save_schedule(schedule, outfile, format=format)
    with open(os.path.join(BASE_PATH, f"{outfile}.{format}"), "rb") as f:
        bot.send_document(
            chat_id=update.message.chat_id, document=f, timeout=10000
        )


def start(bot, update):
    help(bot, update)


def help(bot, update):
    update.message.reply_text(HELP_MESSAGE)
    logger.log(update.message.chat_id, update.message.text, HELP_MESSAGE)


def parse_query(text):
    s = text.lower().split()

    if len(s) == 1:
        return {
            "course_name": "informatica magistrale",
            "partitioning": "",
            "year": 2,
        }

    res = {}
    if s[-1].find("-") > 0 or len(s[-1]) == 2:
        res["partitioning"] = s[-1]
        res["year"] = int(s[-2])
        res["course_name"] = " ".join(s[1:-2])
    else:
        res["partitioning"] = ""
        res["year"] = s[-1]
        res["course_name"] = " ".join(s[1:-1])

    return res


def begin_preference(bot, update, user_data):
    user_data["preference"] = {}
    courses = do.get_all_degree_courses()
    reply_keyboard = [
        [InlineKeyboardButton(course_name, callback_data=course_name)]
        for course_id, course_name in courses
    ]
    reply_markup = InlineKeyboardMarkup(reply_keyboard)
    update.message.reply_text(
        "Scegli il corso di laurea. Per annullare usa /cancel",
        reply_markup=reply_markup,
    )

    return PREF_COURSE


def department(bot, update, user_data):
    raise NotImplementedError


def course(bot, update, user_data):
    course_name = update.callback_query.data.lower()
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id

    user_data["preference"]["course_name"] = course_name
    if course_name.find("magistrale") >= 0:
        reply_keyboard = [
            [
                InlineKeyboardButton("1", callback_data="1"),
                InlineKeyboardButton("2", callback_data="2"),
            ]
        ]
    else:
        reply_keyboard = [
            [
                InlineKeyboardButton("1", callback_data="1"),
                InlineKeyboardButton("2", callback_data="2"),
                InlineKeyboardButton("3", callback_data="3"),
            ]
        ]

    update.callback_query.message.reply_text(
        text="Scegli l'anno", reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return PREF_YEAR


def year(bot, update, user_data):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    try:
        year = int(update.callback_query.data)
        user_data["preference"]["year"] = year
    except ValueError:
        update.callback_query.message.reply_text(
            text="Anno non valido",
            reply_markup=InlineKeyboardMarkup(reply_keyboard),
        )
        return ConversationHandler.END

    reply_keyboard = [
        [InlineKeyboardButton("Nessuno", callback_data="Nessuno")],
        [InlineKeyboardButton("A-L", callback_data="A-L")],
        [InlineKeyboardButton("M-Z", callback_data="M-Z")],
    ]

    update.callback_query.message.reply_text(
        text="Scegli il partizionamento",
        reply_markup=InlineKeyboardMarkup(reply_keyboard),
    )

    return PREF_PARTITIONING


def partitioning(bot, update, user_data):
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    partitioning = text = update.callback_query.data

    if partitioning == "Nessuno":
        user_data["preference"]["partitioning"] = ""
    else:
        user_data["preference"]["partitioning"] = partitioning

    preference = user_data["preference"]
    try:
        result = do.save_preference(user_id=chat_id, **preference)
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
            PREF_PARTITIONING: [
                CallbackQueryHandler(partitioning, pass_user_data=True)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel, pass_user_data=True)],
    )

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("orario", orario))
    dp.add_handler(preference_conversation_handler)
    dp.add_handler(MessageHandler(Filters.text, discorario))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
