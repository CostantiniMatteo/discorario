import requests, json
from datetime import datetime, timedelta
from lecture import Lecture
from degree_course import DegreeCourse
from time_utils import format_hour

url = "http://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib//grid_call.php"
url_courses = "http://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib//combo_call.php"


def get_form(course_id: str, department: str, year: str, date: datetime):
    form = {
        "form-type": "corso",
        "list": 0,
        "anno": 2018,
        "scuola": "",
        "corso": "F1801Q",
        "anno2": "GGG|2",
        "anno2_multi": "GGG|2",
        "visualizzazione_orario": "cal",
        "date": "01-10-2018",
        "periodo_didattico": "",
        "_lang": "en",
        "all_events": 0,
    }

    form["date"] = date.strftime("%d-%m-%Y")
    form["scuola"] = department
    form["corso"] = course_id
    form["anno2"] = year
    form["anno2_multi"] = year

    return form


def fetch_lectures(
    course_id: str, course_name: str, department: str, year: str, date: datetime
):
    form = get_form(course_id, department, year, date)
    response = requests.post(url, form).json()
    lectures = response["celle"]
    first_day = datetime.strptime(response["first_day"], "%d-%m-%Y")

    def get_lecture(c):
        weekday = int(c["giorno"]) - 1
        day = first_day + timedelta(days=weekday)
        b_hours, b_minutes = map(int, c["ora_inizio"].split(":"))
        e_hours, e_minutes = map(int, c["ora_fine"].split(":"))

        return Lecture(
            course=c["nome_insegnamento"],
            room=c["codice_aula"],
            begin=day.replace(hour=b_hours, minute=b_minutes),
            end=day.replace(hour=e_hours, minute=e_minutes),
            day=weekday,
        )

    lectures = [
        get_lecture(c) for c in lectures if "nome_insegnamento" in c.keys()
    ]
    return lectures


def fetch_degree_courses():
    response = requests.get(url_courses).text
    courses = json.loads(response.split("\n")[0].split("=")[1][:-1])
    courses_2018 = courses[0]["elenco"]

    result = [
        DegreeCourse(
            name=c["label"],
            code=c["valore"],
            department=c["scuola"],
            years=c["elenco_anni"],
        )
        for c in courses_2018
    ]

    return result
