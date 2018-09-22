#!/usr/bin/env python
# -*- coding: utf-8 -*-

import six, requests, json, os, sys, imgkit, io, logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil import rrule
from copy import deepcopy
from functools import reduce
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


TOKEN = os.environ['TELEGRAM_TOKEN']
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

url_post = "http://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib//grid_call.php"
post_form = {
    "form-type": "corso",
    "list": 0,
    "anno": 2018,
    "scuola": "Informatica",
    "corso": "F1801Q",
    "anno2": "GGG|2",
    "anno2_multi": "GGG|2",
    "anno2": "GGG|2",
    "visualizzazione_orario": "cal",
    "date": "{}",
    "periodo_didattico": "",
    "_lang": "en",
    "all_events": 0,
}

days = {1: "Lunedì", 2: "Martedì", 3: "Mercoledì", 4: "Giovedì", 5: "Venerdì"}

display_name = {
    "Advanced machine learning": "Advanced\nmachine learning",
    "Computer and robot vision": "Computer and\nrobot vision",
    "Data and computational biology": "Data and\ncomputational biology",
    "Data and text mining": "Data and text mining",
    "Evoluzione dei sistemi software e reverse engineering": "Evoluzione dei\nsistemi software e\nreverse engineering",
    "Information retrieval - t1": "Information retrieval",
    "Information retrieval - t2": "Information retrieval",
    "Information retrieval - tugla": "Information retrieval\ntugla",
    "Intelligenza artificiale": "Intelligenza artificiale",
    "Laboratorio di interaction design": "Laboratorio di\ninteraction design",
    "Large scale data management": "Large scale\ndata management",
    "Tecnologie ed applicazioni dei sistemi distribuiti": "Tecnologie ed applicazioni\ndei sistemi distribuiti",
    "Ubiquitous and context-aware computing": "Ubiquitous and\ncontext-aware computing",
    "Visual information processing and management - TU": "Visual information\nprocessing and\nmanagement",
    "Visual information processing and management - tugea": "Visual information\nprocessing and\nmanagement",
}

colors = {
    "Advanced machine learning": "#FFFCB1",
    "Computer and robot vision": "#FFE6BB",
    "Data and computational biology": "#B9F4FF",
    "Data and text mining": "#F3BAF5",
    "Evoluzione dei sistemi software e reverse engineering": "#F1D0D0",
    "Information retrieval - t1": "#D5FFA4",
    "Information retrieval - t2": "#D5FFA4",
    "Information retrieval - tugla": "#D5FFA4",
    "Intelligenza artificiale": "#FDCBFE",
    "Laboratorio di interaction design": "#A0F3A2",
    "Large scale data management": "#FFE8A4",
    "Tecnologie ed applicazioni dei sistemi distribuiti": "#FFC6A4",
    "Ubiquitous and context-aware computing": "#EEC0C0",
    "Visual information processing and management - TU": "#A7C7D3",
    "Visual information processing and management - tugea": "#A7C7D3",
}

with open('css.css') as f:
    css = f.read()


def split_hours(start_time, end_time):
    sdt = datetime.strptime(start_time, "%H:%M")
    edt = datetime.strptime(end_time, "%H:%M")
    return list(rrule.rrule(rrule.HOURLY, dtstart=sdt, until=edt))

# 8.30 - 20.30
hours = split_hours("8:30", "20:30")
days_list = list(range(1, 6))

day_dict = { k: [] for k in split_hours("8:30", "20:30") }


def stub_read_data():
    with open("response.json") as f:
        response = json.load(f)
        lectures = response["celle"]
        lectures = [
            {
                "name": c["nome_insegnamento"],
                "room": c["codice_aula"],
                "begin": datetime.strptime(c["ora_inizio"], "%H:%M"),
                "end": datetime.strptime(c["ora_fine"], "%H:%M"),
                "day": int(c["giorno"]),
            }
            for c in lectures
        ]
    return lectures


def read_data():
    response = requests.post(url_post, post_form).json()
    lectures = response["celle"]
    lectures = [
        {
            "name": c["nome_insegnamento"],
            "room": c["codice_aula"],
            "begin": datetime.strptime(c["ora_inizio"], "%H:%M"),
            "end": datetime.strptime(c["ora_fine"], "%H:%M"),
            "day": int(c["giorno"]),
        }
        for c in lectures
    ]
    return lectures


def parse_data_by_day(lectures):
    result = {}
    for day in days:
        d = deepcopy(day_dict)
        filtered = filter(lambda l: l["day"] == str(day), lectures)

        for l in filtered:
            hours = int((l["end"] - l["begin"]).total_seconds() / 3600)
            for i in range(hours):
                d[l["begin"] + timedelta(hours=i)].append(l)
        result[day] = d

    return result


def parse_data_by_hour(lectures):
    result = {}
    for hour in hours:
        result[hour] = []
        filtered = list(filter(lambda l: l["begin"]  <= hour < l["end"], lectures))

        for day in days_list:
            day_lectures = list(filter(lambda l: l["day"] == day, filtered))
            result[hour].append(day_lectures)

    return result


def get_html(data_by_hour):
    result = """
<table class="tg">
  <tr>
    <th class="tg-gcbz">Hour</th>
    <th class="tg-n562">Monday</th>
    <th class="tg-n562">Tuestay</th>
    <th class="tg-n562">Wednesday</th>
    <th class="tg-n562">Thursday</th>
    <th class="tg-n562">Friday</th>
  </tr>
"""

    for hour in data_by_hour:
        result += get_row_html(hour, data_by_hour[hour])


    result += "</table>"
    return result


def get_row_html(hour, row):
    result = ""

    overlaps = [len(x) for x in row]
    max_rowspan = max(1, reduce(lambda x, y: x * y, set(overlaps), 1))
    first = True

    hour_template = "    <td class='tg-ocds' rowspan='{}'>{}</td>\n"
    lectures_template = "    <td class='tg-s6z2' rowspan='{}' style='background:{};'>{}<br><br>{}</td>\n"

    for i in range(max(overlaps)):
        result += "  <tr>\n"

        if first:
            result += hour_template.format(
                max_rowspan,
                hour.strftime("%H:%M")
            )
            first = False

        for lectures in row:
            try:
                lecture = lectures[i]
            except IndexError:
                if len(lectures) == 0:
                    result += lectures_template.format(max_rowspan, '', '', '')
                continue

            try:
                rowspan = max_rowspan / len(lectures)
            except ZeroDivisionError:
                rowspan = 1

            result += lectures_template.format(
                rowspan,
                colors[lecture['name']],
                lecture['name'],
                lecture['room']
            )

        result += "  </tr>\n"

    return result


def get_dataframe(data):
    df = pd.DataFrame()
    df["Ora"] = [dt.strftime("%H:%M") for dt in hours]
    for k in days:
        day = days[k]
        df[day] = [
            display_name[x[0]["name"]] if len(x) > 0 else ""
            for x in data[k].values()
        ]
    return df


def get_next_lecture(lectures, query):
    query = query.lower()
    now = datetime.now()
    day = now.weekday() + 1
    hour = now.hour

    if hour >= 20:
        day += 1
        hour = 8
    if hour < 8:
        hour = 8

    template = "La prossima lezione di {} è {} alle {} in aula {}"
    for d in range(day, 6):
        for h in split_hours(f"{hour}:30", "20:30"):
            for lecture in lectures[d][h]:
                if lecture['name'].lower().find(query) >= 0:
                    return template.format(lecture['name'],
                                           days[d],
                                           h.strftime("%H:%M"),
                                           lecture['room'])
    else:
        return "Non ho trovato lezioni per questa settimana"


def render_html(filename, html, css):
    with open('tmp.html', 'w') as text_file:
        text_file.write(css)
        text_file.write(html)

    imgkitoptions = {"format": "png"}
    imgkit.from_file("tmp.html", filename, options=imgkitoptions)



def start(bot, update):
    help(bot, update)


def help(bot, update):
    update.message.reply_text("Cerca un corso o scrivi 'orario' per ricevere l'orario settimanale")


def discorario(bot, update):
    try:
        chat_id = update.message.chat_id
        query = update.message.text.lower()

        if update.message.text.find('orario') >= 0:
            post_form["date"] = f"{datetime.now():%d-%m-%Y}"
            lectures = parse_data_by_hour(read_data())
            render_html('tmp.png', get_html(lectures), css)
            schedule = open('tmp.png', 'rb')
            bot.send_document(chat_id=chat_id, document=schedule, timeout=10000)
        else:
            try:
                lectures = parse_data_by_day(read_data())
                response = get_next_lecture(lectures, query)
            except Exception as e:
                response = "¯\\_(ツ)_/¯"
            update.message.reply_text(response)

    except Exception as e:
        error(bot, update, str(e))


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    updater = Updater(TOKEN)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(MessageHandler(Filters.text, discorario))
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
