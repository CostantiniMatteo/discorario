import requests, json
from time_utils import format_hour, hours

url = (
    "http://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib//grid_call.php"
)
url_courses = (
    "http://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib//combo_call.php"
)


def get_form(course_id, course_name, year, partitioning, date):
    form = {
        "form-type": "corso",
        "list": 0,
        "anno": 2018,
        "scuola": '',
        "corso": "F1801Q",
        "anno2": "GGG|2",
        "anno2_multi": "GGG|2",
        "visualizzazione_orario": "cal",
        "date": "01-10-2018",
        "periodo_didattico": "",
        "_lang": "en",
        "all_events": 0,
    }

    form['date'] = date
    form['corso'] = course_id
    anno = "GGG{}|" +  str(year)
    if partitioning:
        formatted_year = anno.format(
            f"_{partitioning[0].upper()}-{partitioning[-1].upper()}"
        )
        form['anno2'] = formatted_year
    else:
        form['anno2'] = anno.format('')
    form['anno2_multi'] = form['anno2']

    return form


def read_data(course_id, course_name, year, partitioning, date):
    form = get_form(course_id, course_name, year, partitioning, date)
    response = requests.post(url, form).json()
    lectures = response["celle"]
    lectures = [
        {
            "name": c["nome_insegnamento"],
            "room": c["codice_aula"],
            "begin": format_hour(c["ora_inizio"]),
            "end": format_hour(c["ora_fine"]),
            "day": int(c["giorno"]) - 1,
        }
        for c in lectures
    ]
    return lectures


def parse_lectures(lectures):
    result = {}
    for hour in hours:
        result[hour] = []
        filtered = list(
            filter(lambda l: l["begin"] <= hour < l["end"], lectures)
        )

        for day in range(0, 5):
            day_lectures = list(filter(lambda l: l["day"] == day, filtered))
            result[hour].append(day_lectures)

    return result


def fetch_schedule(course_id, course_name, year, partitioning, date):
    lectures = read_data(course_id, course_name, year, partitioning, date)
    return parse_lectures(lectures)
