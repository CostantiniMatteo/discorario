from datetime import datetime
from dateutil import rrule


days = {0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì", 4: "Venerdì"}


def split_hours(start_time, end_time):
    sdt = format_hour(start_time)
    edt = format_hour(end_time)
    return list(rrule.rrule(rrule.HOURLY, dtstart=sdt, until=edt))


def format_hour(dt):
    return datetime.strptime(dt, "%H:%M")


# 8.30 - 20.30
hours = split_hours("8:30", "20:30")
