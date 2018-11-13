from configuration import BASE_PATH, CSS_PATH, COLOR_PATH, DEBUG
from functools import reduce
import pdfkit, imgkit, os


with open(COLOR_PATH) as f:
    colors = f.read().split("\n")[:-1]

with open(CSS_PATH) as f:
    default_css = f.read()


# TODO: Rewrite. Use WeeklySchedule instead of dictionary
def get_html(schedule):
    courses = set(
        l["name"] for row in schedule.values() for day in row for l in day
    )
    color_mapping = dict(zip(courses, colors))

    result = """
<table class="tg">
  <tr>
    <th class="tg-gcbz">Hour</th>
    <th class="tg-n562">Monday</th>
    <th class="tg-n562">Tuesday</th>
    <th class="tg-n562">Wednesday</th>
    <th class="tg-n562">Thursday</th>
    <th class="tg-n562">Friday</th>
  </tr>
"""

    keys = list(schedule.keys())
    for i in range(len(keys) - 1, 0, -1):
        if max(len(x) for x in schedule[keys[i]]) > 0:
            last = i + 1
            break
    else:
        last = len(keys)

    for hour in keys[:last]:
        result += get_row_html(hour, schedule[hour], color_mapping)

    result += "</table>"
    return result


def get_row_html(hour, row, color_mapping):
    result = ""

    overlaps = [max(len(x), 1) for x in row]
    max_rowspan = max(1, reduce(lambda x, y: x * y, set(overlaps), 1))
    rowspans = [max_rowspan // o for o in overlaps]

    hour_template = "    <td class='tg-ocds' rowspan='{}'>{}</td>\n"
    lectures_template = "    <td class='{}' rowspan='{}' style='background:{};'>{}<br><br>{}</td>\n"

    for i in range(max_rowspan):
        result += "  <tr height='50px'>\n"

        first = i == 0
        last = i == max_rowspan - 1
        if first:
            result += hour_template.format(max_rowspan, hour.strftime("%H:%M"))

        classes = "tg-s6z2"
        if first:
            classes += " tg-top-border"
        if last:
            classes += " tg-bottom-border"

        for day in range(len(row)):
            lectures = row[day]
            if i % rowspans[day] == 0:
                try:
                    lecture = lectures[i // rowspans[day]]
                    result += lectures_template.format(
                        classes,
                        rowspans[day],
                        color_mapping[lecture["name"]],
                        lecture["name"],
                        lecture["room"],
                    )
                except Exception as e:
                    result += lectures_template.format(
                        classes, max_rowspan, "", "", ""
                    )

        result += "  </tr>\n"

    return result


def save_html(html, outfile, infile="schedule.html", css=None, format="png"):
    if not css:
        css = default_css

    with open(infile, "w") as text_file:
        text_file.write("<style>" + css + "</style>\n")
        text_file.write(html)

    outfile = os.path.join(BASE_PATH, f"{outfile}.{format}")
    if format == "png":
        if not DEBUG:
            imgkitoptions = {"format": "png", "xvfb": ""}
            imgkit.from_file(infile, outfile, options=imgkitoptions)
        else:
            imgkitoptions = {"format": "png"}
            imgkit.from_file(infile, outfile, options=imgkitoptions)
    elif format == "pdf":
        options = {"page-width": "210", "page-height": "400"}
        if not DEBUG:
            pdfkitconfig = pdfkit.configuration(wkhtmltopdf="./wkhtmltopdf.sh")
            pdfkit.from_file(
                infile, outfile, configuration=pdfkitconfig, options=options
            )
        else:
            pdfkit.from_file(infile, outfile, options=options)


def save_schedule(schedule, outfile, css=None, format="png"):
    html = get_html(schedule)
    save_html(html, outfile, css=css, format=format)
