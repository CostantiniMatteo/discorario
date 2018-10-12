import database as db
from configuration import DEBUG


def log(user_id, message, response, error=""):
    if DEBUG:
        print("user_id:", user_id)
        print("message:", message)
        print("response:", response)
        print("error:", error)

    db.log(user_id, message, response, error)
