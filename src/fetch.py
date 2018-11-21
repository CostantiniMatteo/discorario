import requests, json, re
from datetime import datetime, timedelta
from lecture import Lecture
from degree_course import DegreeCourse
from time_utils import format_hour

url = "http://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib//grid_call.php"
url_courses = "http://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib//combo_call.php"

cached_c = {"last_update": datetime.fromtimestamp(0), "courses": None}
cached_dc = {"last_update": datetime.fromtimestamp(0), "degree_courses": None}


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
    global cached_dc
    if cached_dc["last_update"] + timedelta(hours=1) <= datetime.now():
        response = requests.get(url_courses).text
        degree_courses = json.loads(response.split("\n")[0].split("=")[1][:-1])
        degree_courses_2018 = degree_courses[0]["elenco"]
        cached_dc = {
            "last_update": datetime.now(),
            "degree_courses": degree_courses_2018,
        }
    else:
        degree_courses_2018 = cached_dc["degree_courses"]

    result = [
        DegreeCourse(
            name=c["label"],
            code=c["valore"],
            department=c["scuola"],
            years=[
                {"code": i["valore"], "name": i["label"]}
                for i in c["elenco_anni"]
            ],
        )
        for c in degree_courses_2018
    ]

    return result


def fetch_courses_by_degree_course(
    course_id: str, course_name: str, department: str, year: str
):
    global cached_c
    if cached_c["last_update"] + timedelta(hours=1) <= datetime.now():
        response = requests.get(url_courses).text
        courses = json.loads(response.split("\n")[1].split("=")[1][:-1])
        courses_2018 = courses[0]["elenco"]
        cached_c = {"last_update": datetime.now(), "courses": courses_2018}
    else:
        courses_2018 = cached_c["courses"]

    def to_skip(course, year):
        course_name = course["label"].lower()
        id = course["valore"]
        words = ["prova finale", "erasmus", "stage"]
        year = year.split("|")[-1]
        pattern = re.compile(f"(.+)_(.+)_{year}_(.+)")

        if (year != "0" and pattern.match(id) is None):
            return True

        for w in words:
            if course_name.find(w) >= 0:
                return True
        else:
            return False

    result = set(
        c["label"].strip()
        for c in courses_2018
        if c["valore"].find(course_id) >= 0 and not to_skip(c, year)
    )

    return list(result)
