import sqlite3
import database as db

conn = sqlite3.connect(db.DB_PATH)
c = conn.cursor()

c.execute("""CREATE TABLE user_preference (
    user_id text primary key,
    course_id text,
    course_name text,
    year integer,
    partitioning text
);""")


c.execute("""CREATE TABLE courses (
    course_id text primary key,
    course_name text
);""")

c.execute("""INSERT INTO courses VALUES
    ('F1801Q', 'informatica magistrale'),
    ('E3101Q', 'informatica triennale'),
    ('F9101Q', 'data science magistrale'),
    ('F9201P', 'ttc magistrale');""")

c.execute("""CREATE TABLE user_schedule (
    id integer primary key autoincrement,
    user_id text,
    class_name text
);""")

c.execute("""CREATE TABLE log (
    id integer primary key autoincrement,
    user_id text,
    message text,
    response text,
    error text
);""")

conn.commit()
conn.close()
