import sqlite3
from configuration import DB_PATH


def upsert_user_preference(
    user_id, course_id, course_name, year, partitioning=""
):
    conn = sqlite3.connect(DB_PATH)
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO user_preference
                (user_id, course_id, course_name, year, partitioning)
                VALUES (?, ?, ?, ?, ?);""",
            (user_id, course_id, course_name, year, partitioning),
        )
    conn.close()


def get_user_preference(user_id):
    conn = sqlite3.connect(DB_PATH)
    with conn:
        user_preference = conn.execute(
            "SELECT * FROM user_preference WHERE user_id = ?;", (user_id,)
        ).fetchone()
    conn.close()
    if user_preference:
        return {
            "course_id": user_preference[1],
            "course_name": user_preference[2],
            "year": user_preference[3],
            "partitioning": user_preference[4],
        }
    else:
        return None


def get_course_name(course_id):
    conn = sqlite3.connect(DB_PATH)
    with conn:
        course_name = conn.execute(
            "SELECT * FROM courses WHERE course_id = ?;", (course_id,)
        ).fetchone()
    conn.close()
    return course_name[1]


def get_course_id(course_name):
    conn = sqlite3.connect(DB_PATH)
    with conn:
        course_id = conn.execute(
            "SELECT * FROM courses WHERE course_name = ?;", (course_name,)
        ).fetchone()
    conn.close()
    if course_id:
        return course_id[0]
    else:
        return None


def get_all_courses():
    conn = sqlite3.connect(DB_PATH)
    with conn:
        courses = conn.execute("SELECT * FROM courses;").fetchall()
    conn.close()
    return courses


def save_user_class(user_id, classes):
    entries = [(user_id, cl) for cl in classes]

    conn = sqlite3.connect(DB_PATH)
    with conn:
        conn.executemany("INSERT INTO user_calendar VALUES (?,?);", entries)
    conn.close()


def log(user_id, message, response, error):
    conn = sqlite3.connect(DB_PATH)

    with conn:
        conn.execute(
            """INSERT INTO log (user_id, message, response, error)
            VALUES (?, ?, ?, ?);""",
            (user_id, message, response, error),
        )
    conn.close()
