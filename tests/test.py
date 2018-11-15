import unittest
import sys, os

sys.path.insert(0, os.path.abspath('../src/'))

from lecture import Lecture
import configuration as conf
import init_database as dbutil
import discorario as do
from datetime import datetime

def setUpModule():
    if os.path.exists(conf.DB_PATH):
        os.remove(conf.DB_PATH)
    dbutil.init()
    do.save_preference("1","F1801Q","Informatica (Magistrali)","Informatica","GGG|2")

class PreferencesTest(unittest.TestCase):

    def test_preferences(self):
        do.save_preference("1","F1801Q","Informatica (Magistrali)","Informatica","GGG|2")
        self.assertEqual(do.get_preference("1")["department"], "Informatica")

class DegreeCoursesTest(unittest.TestCase):

    def test_degree_courses(self):
        self.assertEqual(len(do.get_all_degree_courses()), 71)

class AgendaTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        do.save_user_agenda("1",["Information Retrieval","Data and Text Mining"])

    def test_get_weekly_schedule(self):
        self.assertEqual(len(do.get_weekly_schedule("1", datetime.now()).courses), 2)
        schedule = do.get_weekly_schedule("1", datetime.now()).schedule
        slots = 0
        for key, value in schedule.items():
            slots += len([x for x in value if x != []])
        self.assertEqual(slots, 9)

    def test_get_user_agenda(self):
        self.assertEqual(len(do.get_user_agenda("1")), 2)

class NextLectureTest(unittest.TestCase):

    def test_get_next_lecture(self):
        self.assertEqual(type(do.get_next_lecture("1",datetime.now(),"Information Ret")), Lecture)
        self.assertEqual(do.get_next_lecture("1",datetime.now(),"Information Ret").course, "Information retrieval - t2")

if __name__ == '__main__':
    unittest.main()
