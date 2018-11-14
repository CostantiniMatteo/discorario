import unittest
import os
import configuration as conf
import init_database as dbutil
import discorario as do

def setUpModule():
    dbutil.init()
    do.save_preference("1","F1801Q","Informatica (Magistrali)","Informatica","GGG|2")

class PreferencesTest(unittest.TestCase):

    def save_preference_test(self):
        self.assertEqual("1","1")

class SecondTest(unittest.TestCase):

    def test_lower(self):
        self.assertEqual("FOO".lower(), "foo");

def tearDownModule():
    os.remove(conf.DB_PATH)

if __name__ == '__main__':
    unittest.main()
