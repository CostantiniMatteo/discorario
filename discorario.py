from datetime import datetime
from time_utils import days, split_hours
from fetch import fetch_schedule
import rendering
import database as db


def get_next_lecture(query, schedule):
    query = query.lower()
    now = datetime.now()
    # day = now.weekday()
    day = 0
    # hour = now.hour
    hour = 6

    if hour >= 20:
        day += 1
        hour = 8
    if hour < 8:
        hour = 8

    template = "La prossima lezione di {} è {} alle {} in aula {}"
    for d in range(day, 5):
        for h in split_hours(f"{hour}:30", "20:30"):
            for lecture in schedule[h][d]:
                if lecture["name"].lower().find(query) >= 0:
                    return template.format(
                        lecture["name"],
                        days[d],
                        h.strftime("%H:%M"),
                        lecture["room"],
                    )
    else:
        return "¯\\_(ツ)_/¯"


def get_schedule(course_name, year, partitioning, date, course_id=None):
    if not course_id:
        course_id = db.get_course_id(course_name)
    if not course_id:
        return None
    return fetch_schedule(course_id, course_name, year, partitioning, date)


def save_schedule(schedule, outfile):
    rendering.save_schedule(schedule, outfile)
    return True


def save_preference(user_id, course_name, year, partitioning):
    course_id = db.get_course_id(course_name)
    if course_id:
        db.upsert_user_preference(user_id, course_id, course_name, year, partitioning)
        return True
    else:
        return False


def get_user_preference(user_id):
    return db.get_user_preference(user_id)
