import os

DEBUG = os.environ.get("DEBUG")
TOKEN = os.environ.get("TELEGRAM_TOKEN")

BASE_PATH = os.pardir
RESOURCES = "res"
DB_PATH = os.path.join(BASE_PATH, "discorario.db")
CSS_PATH = os.path.join(BASE_PATH, RESOURCES, "css.css")
COLOR_PATH = os.path.join(BASE_PATH, RESOURCES, "colors.txt")
