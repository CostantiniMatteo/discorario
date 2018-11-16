from datetime import datetime, timedelta
from time_utils import days, split_hours
from typing import List
import fetch
import rendering
import database as db
from weekly_schedule import WeeklySchedule

# NextLectureTest
def get_next_lecture(user_id: str, date: datetime, query: str):
    query = query.lower()
    schedule = WeeklySchedule.from_user(user_id, date)

    next_lecture = schedule.get_next_lecture(query, date)
    if not next_lecture:
        next_monday = date + timedelta(days=7 - date.weekday())
        next_lecture = schedule.get_next_lecture(query, next_monday)

    return next_lecture


# AgendaTest
def get_weekly_schedule(user_id: str, date: datetime):
    return WeeklySchedule.from_user(user_id, date)


# PreferencesTest
def save_preference(
    user_id: str, course_id: str, course_name: str, department: str, year: str
):
    try:
        db.upsert_user_preference(
            user_id, course_id, course_name, department, year
        )
    except Exception:
        return False
    else:
        return True


# PreferencesTest
def get_preference(user_id: str):
    return db.get_user_preference(user_id)


# DegreeCoursesTest
def get_all_degree_courses():
    return fetch.fetch_degree_courses()


# AgendaTest
def get_all_departments():
    degree_courses = get_all_degree_courses()
    return set(course.department for course in degree_courses)


# AgendaTest
def save_user_agenda(user_id: str, courses: List[str]):
    db.save_user_agenda(user_id, courses)


# AgendaTest
def get_user_agenda(user_id: str):
    return db.get_user_agenda(user_id)


def get_courses(course_id: str, course_name: str, department: str, year: str):
    return fetch.fetch_courses_by_degree_course(course_id, course_name, department, year)
