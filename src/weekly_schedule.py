from dataclasses import dataclass
from datetime import datetime, timedelta
from time_utils import format_hour, hours, split_hours
from typing import List, Dict
from lecture import Lecture
from fetch import fetch_lectures


class WeeklySchedule:
    @staticmethod
    def from_user(user_id: str, date: datetime=None):
        import discorario as do
        if not date:
            date = datetime.now()
        preference = do.get_preference(user_id)
        courses = do.get_user_agenda(user_id)
        lectures = fetch_lectures(date=date, **preference)
        return WeeklySchedule(lectures, courses)


    def __init__(self, lectures: List[Lecture], courses: List[str]=[]):
        self.schedule = {}
        self.courses = courses

        def is_course_in_agenda(lecture: Lecture, courses: List[str]):
            for course in courses:
                if lecture.course.lower().find(course.lower()) >= 0:
                    return True
            else:
                return False

        for hour in hours:
            self.schedule[hour] = []

            filtered = [
                Lecture(
                    course=l.course,
                    room=l.room,
                    begin=l.begin.replace(hour=hour.hour, minute=hour.minute),
                    end=l.end.replace(hour=(hour + timedelta(hours=1)).hour),
                    day=l.day,
                )
                for l in lectures
                if l.begin.hour <= hour.hour < l.end.hour and is_course_in_agenda(l, self.courses)
            ]


            for day in range(0, 5):
                day_lectures = list(filter(lambda l: l.day == day, filtered))
                self.schedule[hour].append(day_lectures)


    def get_next_lecture(self, query: str, date: datetime):
        day = date.weekday()
        hour = date.hour

        if hour >= 20:
            day += 1
            hour = 8
        if hour < 8:
            hour = 8

        curr_hours = split_hours(f"{hour}:30", "20:30")
        for d in range(day, 5):
            for h in curr_hours:
                for lecture in self.schedule[h][d]:
                    if lecture.course.lower().find(query) >= 0:
                        return lecture
            curr_hours = hours
        else:
            return None
