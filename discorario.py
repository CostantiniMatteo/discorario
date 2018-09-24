from datetime import datetime
from time_utils import days, split_hours
from fetch import fetch_schedule
import rendering


def get_next_lecture(query, schedule=None):
    if not schedule:
        schedule = get_schedule()

    query = query.lower()
    now = datetime.now()
    day = now.weekday()
    hour = now.hour

    if hour >= 20:
        day += 1
        hour = 8
    if hour < 8:
        hour = 8

    template = "La prossima lezione di {} è {} alle {} in aula {}"
    for d in range(day, 5):
        for h in split_hours(f"{hour}:30", "20:30"):
            for lecture in schedule[h][day]:
                if lecture["name"].lower().find(query) >= 0:
                    return template.format(
                        lecture["name"],
                        days[d],
                        h.strftime("%H:%M"),
                        lecture["room"],
                    )
    else:
        return "Non ho trovato lezioni per questa settimana"


def get_schedule(
    course="Informatica", course_id="F1801Q", year=2, date="01-10-2018"
):
    return fetch_schedule(course, course_id, year, date)


def save_schedule(schedule, outfile):
    rendering.save_schedule(schedule, outfile)
