from datetime import datetime, timedelta
from time_utils import days, split_hours
from fetch import fetch_lectures, fetch_degree_courses
import rendering
import database as db
from weekly_schedule import WeeklySchedule


def get_next_lecture(user_id: str, date: datetime, query: str):
    query = query.lower()
    schedule = WeeklySchedule.from_user(user_id, date)

    next_lecture = schedule.get_next_lecture(query, date)
    if not next_lecture:
        next_monday = date + timedelta(days=7 - date.weekday())
        next_lecture = schedule.get_next_lecture(query, next_monday)

    return next_lecture
    # if not next_lecture:
    #     return "¯\\_(ツ)_/¯"

    # template = "La prossima lezione di {course} è {day} alle {hour} in aula {room}"

    # display_day = days[lecture.begin.weekday()]
    # if d == date.

    # display_day = days[d]
    # if d == now.weekday():
    #     display_day = "oggi"
    # if d == now.weekday() + 1:
    #     display_day = "domani"
    # return template.format(
    #     lecture["name"],
    #     display_day,
    #     h.strftime("%H:%M"),
    #     lecture["room"],
    # )


def get_weekly_schedule(user_id: str, date: datetime):
    schedule = WeeklySchedule.from_user(user_id, date)
    return schedule


def save_preference(user_id, course_id, course_name, department, year):
    db.upsert_user_preference(user_id, course_id, course_name, department, year)


def get_preference(user_id):
    return db.get_user_preference(user_id)


def get_all_degree_courses():
    return fetch_degree_courses()


def save_user_agenda(user_id, courses):
    db.save_user_agenda(user_id, courses)


def get_user_agenda(user_id):
    return db.get_user_agenda(user_id)
