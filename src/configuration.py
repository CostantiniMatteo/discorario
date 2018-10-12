import os

try:
    os.environ["DEBUG"]
    DEBUG = True
except:
    DEBUG = False

TOKEN = os.environ["TELEGRAM_TOKEN"]

if DEBUG:
    BASE_PATH = "/Users/matteo/git/discorario"
else:
    BASE_PATH = "/home/matteo_angelo_costantini/discorario"
RESOURCES = "res"
DB_PATH = os.path.join(BASE_PATH, "discorario.db")
CSS_PATH = os.path.join(BASE_PATH, RESOURCES, "css.css")
COLOR_PATH = os.path.join(BASE_PATH, RESOURCES, "colors.txt")
