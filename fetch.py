import requests, json
from time_utils import format_hour, hours


url = (
    "http://gestioneorari.didattica.unimib.it/PortaleStudentiUnimib//grid_call.php"
)

form = {
    "form-type": "corso",
    "list": 0,
    "anno": 2018,
    "scuola": "Informatica",
    "corso": "F1801Q",
    "anno2": "GGG|2",
    "anno2_multi": "GGG|2",
    "visualizzazione_orario": "cal",
    "date": "01-10-2018",
    "periodo_didattico": "",
    "_lang": "en",
    "all_events": 0,
}


def read_data(course, course_id, year, date):
    form["scuola"] = course
    form["corso"] = course_id
    form["anno2"] = form["anno2_multi"] = f"GGG|{year}"
    form["date"] = date

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


def fetch_schedule(course, course_id, year, date):
    lectures = read_data(course, course_id, year, date)
    return parse_lectures(lectures)


def stub_read_data():
    with open("response.json") as f:
        response = json.load(f)
        lectures = response["celle"]
        lectures = [
            {
                "name": c["nome_insegnamento"],
                "room": c["codice_aula"],
                "begin": format_hour(c["ora_inizio"]),
                "end": format_hour(c["ora_fine"]),
                "day": int(c["giorno"]),
            }
            for c in lectures
        ]

    return lectures
