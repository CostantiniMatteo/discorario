from functools import reduce
import imgkit


with open("colors.txt") as f:
    colors = f.read().split("\n")[:-1]

with open("css.css") as f:
    default_css = f.read()


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
    first = True

    hour_template = "    <td class='tg-ocds' rowspan='{}'>{}</td>\n"
    lectures_template = (
        "    <td class='tg-s6z2' rowspan='{}' style='background:{};'>{}<br><br>{}</td>\n"
    )

    for i in range(max(overlaps)):
        result += "  <tr height=100px>\n"

        if first:
            result += hour_template.format(max_rowspan, hour.strftime("%H:%M"))
            first = False

        for lectures in row:
            try:
                lecture = lectures[i]
            except IndexError:
                if len(lectures) == 0:
                    result += lectures_template.format(1, "", "", "")
                continue

            try:
                rowspan = max_rowspan / len(lectures)
            except ZeroDivisionError:
                rowspan = 1

            result += lectures_template.format(
                rowspan,
                color_mapping[lecture["name"]],
                lecture["name"],
                lecture["room"],
            )

        result += "  </tr>\n"

    return result


def save_html(html, outfile, infile="schedule.html", css=None):
    if not css:
        css = default_css

    with open(infile, "w") as text_file:
        text_file.write("<style>" + css + "</style>\n")
        text_file.write(html)

    # imgkitoptions = {"format": "png"}
    # imgkit.from_file(infile, outfile, options=imgkitoptions)


def save_schedule(schedule, outfile, css=None):
    html = get_html(schedule)
    save_html(html, outfile, css=css)
