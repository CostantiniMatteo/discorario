import sqlite3
from configuration import DB_PATH


def upsert_user_preference(
    user_id, course_id, course_name, year, partitioning=""
):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """INSERT OR REPLACE INTO user_preference
    (user_id, course_id, course_name, year, partitioning)
    VALUES (?, ?, ?, ?, ?);""",
        (user_id, course_id, course_name, year, partitioning),
    )
    conn.commit()
    conn.close()


def get_user_preference(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM user_preference WHERE user_id = ?;", (user_id,))
    user_preference = c.fetchone()
    conn.commit()
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
    c = conn.cursor()
    c.execute("SELECT * FROM courses WHERE course_id = ?;", (course_id,))
    course_name = c.fetchone()
    conn.commit()
    conn.close()
    return course_name[1]


def get_course_id(course_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM courses WHERE course_name = ?;", (course_name,))
    course_id = c.fetchone()
    conn.commit()
    conn.close()
    if course_id:
        return course_id[0]
    else:
        return None


def get_all_courses():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM courses;")
    courses = c.fetchall()
    return courses


def log(user_id, message, response, error):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """INSERT INTO log (user_id, message, response, error)
    VALUES (?, ?, ?, ?);""",
        (user_id, message, response, error),
    )
    conn.commit()
    conn.close()
