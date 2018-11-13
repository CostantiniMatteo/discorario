import sqlite3
from configuration import DB_PATH


def upsert_user_preference(
    user_id, course_id, course_name, department, year=""
):
    conn = sqlite3.connect(DB_PATH)
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO user_preference
                (user_id, course_id, course_name, department, year)
                VALUES (?, ?, ?, ?, ?);""",
            (user_id, course_id, course_name, department, year),
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
            "department": user_preference[3],
            "year": user_preference[4],
        }
    else:
        return None


def save_user_agenda(user_id, courses):
    entries = [(user_id, course) for course in courses]

    conn = sqlite3.connect(DB_PATH)
    with conn:
        conn.executemany(
            "INSERT OR REPLACE INTO user_agenda VALUES (?,?);", entries
        )
    conn.close()


def get_user_agenda(user_id):
    conn = sqlite3.connect(DB_PATH)
    with conn:
        user_agenda = conn.execute(
            "SELECT course_name FROM user_agenda WHERE user_id = ?;", (user_id,)
        ).fetchall()

    if user_agenda:
        return [item[0] for item in user_agenda]


def log(user_id, message, response, error):
    conn = sqlite3.connect(DB_PATH)

    with conn:
        conn.execute(
            """INSERT INTO log (user_id, message, response, error)
            VALUES (?, ?, ?, ?);""",
            (user_id, message, response, error),
        )
    conn.close()
