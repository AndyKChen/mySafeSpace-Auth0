from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# function to return list of friends   
def friends():
    username = session["username"]

    user_id = db.execute("SELECT id FROM users WHERE username=:username", {"username":username}).fetchone()[0]

    friends = db.execute("SELECT users.username FROM friendships \
        JOIN users ON users.id = friendships.person_id1 \
        WHERE friendships.person_id2=:user_id \
        UNION SELECT users.username FROM friendships \
        JOIN users ON users.id = friendships.person_id2\
        WHERE friendships.person_id1=:user_id",
        {"user_id":user_id, "user_id":user_id}).fetchall()

    return friends