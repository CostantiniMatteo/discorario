from datetime import datetime
from dateutil import rrule


days = {0: "Lunedì", 1: "Martedì", 2: "Mercoledì", 3: "Giovedì", 4: "Venerdì"}


def split_hours(start_time, end_time):
    sdt = format_hour(start_time)
    edt = format_hour(end_time)
    return list(rrule.rrule(rrule.HOURLY, dtstart=sdt, until=edt))


def format_hour(hours, day=None):
    if day and hours:
        return datetime.strptime(" ".join([day, hours]), "%d-%m-%Y %H:%M")

    return datetime.strptime(hours, "%H:%M")


# 8.30 - 20.30
hours = split_hours("8:30", "20:30")
