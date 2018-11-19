import database as db
from configuration import DEBUG


def log(user, message, response, error=""):
    if DEBUG:
        print("user_id:", user.id)
        print("message:", message)
        print("response:", response)
        print("error:", error)

    db.log(user, message, response, error)
