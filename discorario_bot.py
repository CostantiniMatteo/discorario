#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime, io, logging
from PIL import Image
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

DRIVER = 'Firefox'
TOKEN = 'key'
BASE_URL = "http://orariolezioni.didattica.unimib.it/Orario/Informatica/2017-2018/Settimana-{}_{}/Curricula/{}_{}_{}_Percorsocomune{}_{}.html"
FIRST_WEEK = datetime.date(2018, 2, 26).isocalendar()[1]
CDL = {
        'Informatica': {'Triennale': ('Informatica', 'E3101Q'), 'Magistrale': ('Informatica', 'F1801Q')},
        'Data Science': ('Datascience', 'F9101Q'),
        'TTC': ('Teoriaetecnologiadellacomunicazione', 'F9201P')
}
USER_PREFERENCES = {}
COURSE, DEGREE, YEAR, SEMESTER, AL_MZ, CONFIGURATION = range(6)


def get_week():
    return datetime.datetime.now().isocalendar()[1]  - FIRST_WEEK + 1


def start(bot, update):
    reply_keyboard = [['Data Science', 'TTC'], ["Informatica"]]

    # if update.effective_user.id == 214977134:
    #     update.message.reply_text("Continuo a non dirtelo a te, Marta...")
    #     return ConversationHandler.END

    update.message.reply_text("Scegli il corso di laurea",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return COURSE


def course(bot, update, user_data):
    user = update.message.from_user
    user_data['course'] = update.message.text
    logger.info("Corso di %s: %s", user.first_name, update.message.text)

    if update.message.text == 'TTC':
        user_data['degree'] = 'Magistrale'
        reply_keyboard = [['1', '2']]
        update.message.reply_text('Anno?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return YEAR

    if update.message.text == 'Data Science':
        user_data['degree'] = 'Magistrale'
        user_data['year'] = '1'
        reply_keyboard = [['1', '2']]
        update.message.reply_text('Semestre?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return SEMESTER

    if update.message.text == 'Informatica':
        reply_keyboard = [['Triennale', 'Magistrale']]
        update.message.reply_text('Triennale o Magistrale?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
        return DEGREE

    raise Exception('Corso di laurea non valido')


def degree(bot, update, user_data):
    user = update.message.from_user
    user_data['degree'] = update.message.text
    logger.info("Degree of %s: %s", user.first_name, update.message.text)

    reply_keyboard = [['1', '2']]
    if update.message.text == 'Triennale':
        reply_keyboard = [['1', '2', '3']]
    update.message.reply_text('Anno?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return YEAR


def year(bot, update, user_data):
    user = update.message.from_user
    user_data['year'] = update.message.text
    logger.info("Year of %s: %s", user.first_name, update.message.text)

    reply_keyboard = [['1', '2']]
    update.message.reply_text('Semestre?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    return SEMESTER


def semester(bot, update, user_data):
    user = update.message.from_user
    user_data['semester'] = update.message.text
    logger.info("Semester of %s: %s", user.first_name, update.message.text)

    if user_data['degree'] == 'Triennale' and user_data['year'] != 3:
        reply_keyboard = [['A-L', 'M-Z']]
        update.message.reply_text('A-L o M-Z?',
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

        return AL_MZ

    if 'configuration' in user_data.keys() and user_data['configuration']:
        save_configuration(user_data)
        user_data['configuration'] = False
    else:
        send_schedule(bot, update, user_data['course'], user_data['degree'], user_data['year'], user_data['semester'])
    return ConversationHandler.END


def al_mz(bot, update, user_data):
    user = update.message.from_user
    user_data['al_mz'] = update.message.text
    logger.info("Group of %s: %s", user.first_name, update.message.text)

    if 'configuration' in user_data.keys() and user_data['configuration']:
        save_configuration(user_data)
        user_data['configuration'] = False
    else:
        send_schedule(bot, update, user_data['course'], user_data['degree'], user_data['year'], user_data['semester'], user_data['al_mz'])

    return ConversationHandler.END


def cancel(bot, update, user_data):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Scelta annullata.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def send_schedule(bot, update,  course, degree, year, semester, group=''):
    week = get_week()
    semester_id = 90 if semester == 1 else 112
    cdl_id = CDL[course][1] if course != 'Informatica' else CDL[course][degree][1]
    cdl_name = CDL[course][0] if course != 'Informatica' else CDL[course][degree][0]

    url = BASE_URL.format(week, semester_id, cdl_name, degree.lower(), year, group, cdl_id)

    if DRIVER == 'Firefox':
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver', firefox_options=options)
        driver.get(url)
        driver.set_window_size(1920, 1080)
        table = driver.find_element_by_class_name('timegrid')
        image_data = table.screenshot_as_png
        image = Image.open(io.BytesIO(image_data))
        result = image
    else:
        driver = webdriver.PhantomJS()
        driver.get(url)
        driver.set_window_size(1920, 1080)
        table = driver.find_element_by_class_name('timegrid')
        x, y = table.location.values()
        dy, dx = table.size.values()
        image_data = table.screenshot_as_png
        image = Image.open(io.BytesIO(image_data))
        result = image.crop((x, y, x+dx, y+dy)).convert('RGB')

    bio = io.BytesIO()
    bio.name = "orario_settimana_{}".format(week)
    result.save(bio, 'PNG')
    bio.seek(0)

    bot.send_document(chat_id=update.message.chat_id, document=bio)


def lazy(bot, update):
    logger.info("%s is lazy: %s", update.message.from_user.first_name, update.message.text)
    update.message.reply_text('Invio gli orari della magistrale in informatica (secondo semestre). Per gli altri orari: /start')
    send_schedule(bot, update, 'Informatica', 'Magistrale', '1', '2')


def begin_configuration(bot, update, user_data):
    logger.info("Configuration (%s): %s", update.message.from_user.first_name, update.message.text)
    update.message.reply_text('Not implemented')
    user_data['configuration'] = True
    return COURSE

def configuration(bot, update, user_data):
    logger.info("Configuration (%s): %s", update.message.from_user.first_name, update.message.text)
    update.message.reply_text('Not implemented')

    return ConversationHandler.END


def save_configuration(bot, update, user_data):
    pass


def aula(bot, update):
    logger.info("Aula (%s): %s", update.message.from_user.first_name, update.message.text)
    if update.effective_user.id not in USER_PREFERENCES.keys():
        update.message.reply_text('Non conosco i tuoi corsi. Per impostare le preferenze utilizza il comando /configure')

    aula = get_aula(**USER_PREFERENCES[update.effective_user.id])

    return ConversationHandler.END

def get_aula(course, degree, year, semester, al_mz=None, courses=[]):
    week = get_week()


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      CommandHandler('configure', begin_configuration, pass_user_data=True),
                      CommandHandler('aula', aula),
                      RegexHandler('.+', lazy),
        ],

        states={
            COURSE: [RegexHandler('^(Data Science|TTC|Informatica)$',
                        course, pass_user_data=True)],

            DEGREE: [RegexHandler('^(Triennale|Magistrale)$',
                        degree, pass_user_data=True)],

            YEAR: [RegexHandler('^(1|2|3)$', year, pass_user_data=True)],

            SEMESTER: [RegexHandler('^(1|2)$', semester, pass_user_data=True)],

            AL_MZ: [RegexHandler('^(A-L|M-Z)$', al_mz, pass_user_data=True)],

            CONFIGURATION: [RegexHandler('.+', configuration, pass_user_data=True)],
        },

        fallbacks=[CommandHandler('cancel', cancel, pass_user_data=True)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
