import sqlite3
from configuration import DB_PATH


def init():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """CREATE TABLE user_preference (
        user_id text primary key,
        course_id text,
        course_name text,
        department text,
        year text
    );"""
    )

    c.execute(
        """CREATE TABLE user_agenda (
        user_id text,
        course_name text
    );"""
    )

    c.execute(
        """CREATE TABLE log (
        id integer primary key autoincrement,
        user_id text,
        message text,
        response text,
        error text
    );"""
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init()
