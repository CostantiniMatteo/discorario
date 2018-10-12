from datetime import datetime
from time_utils import days, split_hours
from fetch import fetch_schedule
import rendering
import database as db


def get_next_lecture(query, schedule):
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
            for lecture in schedule[h][d]:
                if lecture["name"].lower().find(query) >= 0:
                    display_day = days[d]
                    if d == now.weekday():
                        display_day = "oggi"
                    if d == now.weekday() + 1:
                        display_day = "domani"
                    return template.format(
                        lecture["name"],
                        display_day,
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
    # TODO: Filter courses when custom calendar is implemented
    return fetch_schedule(course_id, course_name, year, partitioning, date)


def save_schedule(schedule, outfile, format="png"):
    rendering.save_schedule(schedule, outfile, format=format)
    return True


def save_preference(user_id, course_name, year, partitioning):
    course_id = db.get_course_id(course_name)
    if course_id:
        db.upsert_user_preference(
            user_id, course_id, course_name, year, partitioning
        )
        return True
    else:
        return False


def get_user_preference(user_id):
    return db.get_user_preference(user_id)


def get_all_courses():
    return db.get_all_courses()


# TODO: Update custom calendar
