import database as db


def log(user_id, message, response, error='', stdout=True):
    if stdout:
        print("user_id:", user_id)
        print("message:", message)
        print("response:", response)
        print("error:", error)

    db.log(user_id, message, response, error)
