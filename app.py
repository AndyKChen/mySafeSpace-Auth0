import os
import uuid

from flask import Flask, session, flash, redirect, render_template, request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime, timedelta

from models import init_db

from helpers import *

# for api handling #
import json 
import requests 

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app.secret_key = os.getenv("SECRET")

api_key = os.getenv("API_KEY")
url_perspective = ('https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key=' + api_key)
url_nlp = ('https://language.googleapis.com/v1/documents:analyzeSentiment?key=' + api_key)


socketio = SocketIO(app)

# Set up database

engine = create_engine(os.getenv("DATABASE_URL"))
init_db(engine)
db = scoped_session(sessionmaker(bind=engine))


names = dict()


@app.route("/")
@login_required
def index():
    messages = dict()

    # Get the list of friends
    friend_list = friends(session["user_id"])

    # Fetch user info with `.mappings()` to access columns by name
    user_info = db.execute(
        text("SELECT * FROM user_info WHERE username=:username"),
        {"username": session["username"]}
    ).mappings().fetchone()

    for friend in friend_list:
        username = friend['username']  # Accessing by column name instead of index
        
        # Fetch the friend's id
        friend_id = db.execute(
            text("SELECT id FROM users WHERE username=:username"),
            {"username": username}
        ).mappings().fetchone()['id']

        # Fetch the friend's first name
        name = db.execute(
            text("SELECT first FROM users WHERE username=:username"),
            {"username": username}
        ).mappings().fetchone()['first']

        try:
            # Fetch the last message between the session user and the friend
            msg = db.execute(
                text("SELECT message FROM messages WHERE (sender_id=:sender_id AND reciever_id=:reciever_id) OR (sender_id=:reciever_id and reciever_id=:sender_id) ORDER BY time DESC"),
                {"sender_id": session["user_id"], "reciever_id": friend_id}
            ).mappings().fetchone()['message']
        except TypeError:
            msg = "No chats yet!"

        # Update the messages and names dictionaries
        messages.update({username: msg})
        names.update({username: name})

    # Fetch avatars
    avatars = get_avatars()

    # Render the template
    return render_template("index.html", friends=friend_list, user_info=user_info, avatars=avatars, messages=messages)


@app.route("/chat/<friend>")
@login_required
def chat(friend):

    # Get the list of friends
    friend_list = friends(session["user_id"])

    # Fetch the friend's ID by username
    p2_id = db.execute(
        text("SELECT id FROM users WHERE username=:username"),
        {"username": friend}
    ).mappings().fetchone()["id"]

    # Set the friend and chat session details
    session['friend'] = friend
    session['chat_id'] = db.execute(
        text("SELECT chat_id FROM chat_ids WHERE (p1_id=:p1_id AND p2_id=:p2_id) OR (p1_id=:p2_id AND p2_id=:p1_id)"),
        {"p1_id": session["user_id"], "p2_id": p2_id}
    ).mappings().fetchone()["chat_id"]

    # Fetch friend ID again
    friend_id = db.execute(
        text("SELECT id FROM users WHERE username=:username"),
        {"username": friend}
    ).mappings().fetchone()["id"]

    # Fetch the messages between the user and the friend
    messages = db.execute(
        text("SELECT messages.sender_id, messages.reciever_id, messages.time, messages.message FROM messages \
              JOIN chat_ids ON chat_ids.chat_id = messages.conversation_id \
              WHERE p1_id=:p1_id AND p2_id=:p2_id"),
        {"p1_id": session["user_id"], "p2_id": friend_id}
    ).mappings().fetchall()

    # Fetch avatars for the chat
    avatars = get_avatars()

    # Render the template
    return render_template("chat.html", messages=messages, friends=friend_list, name=friend, avatars=avatars, names=names)



@app.route("/register", methods=["GET","POST"])
def register():

    session.clear()

    if request.method == "POST":

        # Get user inputed registration info
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("pass")
        check_pass = request.form.get("re_pass")
        first = request.form.get("firstname")
        last = request.form.get("lastname")

        # check for existing user
        checkUser = db.execute(text("SELECT * from users WHERE username=:username"),
            {"username":username}).fetchone()

        checkEmail = db.execute(text("SELECT * from users WHERE email=:email"),
            {"email":email}).fetchone()

        if checkUser:
            flash("This username already exists.")
            return render_template("register.html")

        elif checkEmail:
            flash("This email already exists.")
            return render_template("register.html")

        # ensure pw of length 5+
        elif len((str)(password)) < 5:
            flash("Please choose a password of at least 6 characters.")
            return render_template("register.html")

        # ensure pw match
        elif password != check_pass:
            flash("Passwords don't match!")
            return render_template("register.html")

        # encrypt pw
        pw = sha256_crypt.hash((str)(password))

        # insert new user into db
        db.execute(text("INSERT INTO users (username, password, email, first, last) VALUES (:username, :password, :email, :first, :last)"),
            {"username":username, "password":pw, "email":email, "first": first, "last":last})
        db.commit()

        # insert default user info into db
        db.execute(text("INSERT INTO user_info (username, avatar, facebook, twitter, instagram) VALUES (:username, :avatar, :facebook, :twitter, :instagram)"), 
            {"username": username, "avatar": "default", "facebook": "N/A", "twitter": "N/A", "instagram": "N/A"})
        db.commit()

        flash("Account Created!")
        return redirect("login")

    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    session.clear()

    if request.method == "POST":
        username = request.form.get("user")
        password = request.form.get("pass")

        # Fetch the user data by username or email using mappings to access columns by name
        checkUser = db.execute(
            text("SELECT * from users WHERE username=:username OR email=:username"),
            {"username": username}
        ).mappings().fetchone()

        if not checkUser:
            flash("Username or Email does not exist.")
            return render_template("login.html")

        # Check if the password matches the hash stored in the database
        elif not sha256_crypt.verify(password, checkUser["password"]):
            flash("Incorrect Password")
            return render_template("login.html")

        # Store user information in the session
        session["user_id"] = checkUser["id"]
        session["username"] = checkUser["username"]
        session["name"] = checkUser["first"]

        session.permanent = True

        return redirect("/")

    else:
        return render_template("login.html")



@app.route("/logout")
@login_required
def logout():
    session.clear()

    return redirect("/login")


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        # Get user-submitted info from the form
        title = request.form.get("title")
        topic = request.form.get("topic")
        picture = request.form.get("picture")

        # Default the picture to "default" if no selection is made
        if picture is None:
            picture = "default"

        # Create a unique channel ID using UUID
        channel_id = uuid.uuid1().hex

        # Insert the new channel into the database
        db.execute(
            text("INSERT INTO channels (channel_id, title, topic, picture) VALUES (:channel_id, :title, :topic, :picture)"),
            {"channel_id": channel_id, "title": title, "topic": topic, "picture": picture}
        )
        db.commit()

        # Flash success message and redirect back to the create page
        flash("Channel Created")
        return redirect("/create")

    # Render the create.html template if method is GET
    return render_template("create.html")



@app.route("/friends", methods=["GET", "POST"])
@login_required
def friends():
    username = session["username"]
    user_id = session["user_id"]

    # Get the friend list
    friend_list = friends(user_id)

    if request.method == "POST":
        # Get the username of the friend to add
        friend = request.form.get("friend")

        # Search for the user ID of the friend in the database
        try:
            friend_data = db.execute(
                text("SELECT id FROM users WHERE username=:username"),
                {"username": friend}
            ).mappings().fetchone()

            if not friend_data:
                flash("Sorry, this user does not exist.")
                return redirect("/friends")

            friend_id = friend_data["id"]

            if friend_id == user_id:
                flash("You cannot add yourself!")
                return redirect("/friends")

        except TypeError:
            flash("Sorry, this user does not exist.")
            return redirect("/friends")

        # Check if the user is already friends with the selected user
        existing = db.execute(
            text("SELECT * FROM friendships WHERE person_id1=:user_id AND person_id2=:friend_id"),
            {"user_id": user_id, "friend_id": friend_id}
        ).fetchone()

        if existing:
            flash("You are already friends with this person!")
            return redirect("/friends")

        # Insert the new friendship into the database
        db.execute(
            text("INSERT INTO friendships (person_id1, person_id2, date) VALUES (:p1, :p2, :date)"),
            {"p1": user_id, "p2": friend_id, "date": datetime.date(datetime.now())}
        )
        db.commit()

        # Create a unique conversation ID
        chat_id = uuid.uuid1().hex

        # Insert the chat ID for both the user and the friend
        db.execute(
            text("INSERT INTO chat_ids (chat_id, p1_id, p2_id) VALUES (:chat_id, :p1_id, :p2_id)"),
            {"chat_id": chat_id, "p1_id": user_id, "p2_id": friend_id}
        )
        db.commit()

        db.execute(
            text("INSERT INTO chat_ids (chat_id, p1_id, p2_id) VALUES (:chat_id, :p1_id, :p2_id)"),
            {"chat_id": chat_id, "p1_id": friend_id, "p2_id": user_id}
        )
        db.commit()

        flash("Friend Added!")
        return redirect("/friends")

    if request.method == "GET":
        # Fetch and update the names and avatars for the friend list
        for friend in friend_list:
            name = db.execute(
                text("SELECT first FROM users WHERE username=:username"),
                {"username": friend['username']}
            ).mappings().fetchone()["first"]
            names.update({friend['username']: name})

        avatars = get_avatars()

        return render_template("friends.html", friends=friend_list, avatars=avatars, names=names)


       



@app.route("/channels")
@login_required
def channels():

    # Fetch user info using .mappings() to access fields by column names
    user_info = db.execute(
        text("SELECT * FROM user_info WHERE username=:username"),
        {"username": session["username"]}
    ).mappings().fetchone()

    # Fetch channels and access fields by column names
    channels = db.execute(
        text("SELECT * FROM channels")
    ).mappings().fetchall()

    return render_template("channels.html", user_info=user_info, channels=channels)


@app.route("/channel/<channel_id>")
@login_required
def chats(channel_id):

    # Fetch all channels for the side menu
    channels = db.execute(
        text("SELECT * FROM channels")
    ).mappings().fetchall()

    # Fetch the current channel's information
    current_channel = db.execute(
        text("SELECT * FROM channels WHERE channel_id=:channel_id"),
        {"channel_id": channel_id}
    ).mappings().fetchone()

    # Fetch the user information
    user_info = db.execute(
        text("SELECT * FROM user_info WHERE username=:username"),
        {"username": session["username"]}
    ).mappings().fetchone()

    # Fetch all messages for the current channel
    messages = db.execute(
        text("SELECT * FROM channel_messages WHERE channel_id=:channel_id"),
        {"channel_id": channel_id}
    ).mappings().fetchall()

    # Store the channel_id in session
    session["channel_id"] = channel_id

    # Fetch avatars
    avatars = get_avatars()

    # Render the template
    return render_template("channel_chat.html", channels=channels, avatars=avatars, user_info=user_info, messages=messages, current_channel=current_channel)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        # Check if the user has changed their avatar
        if request.form.get("avatar"):
            avatar = request.form.get("avatar")

            db.execute(
                text("UPDATE user_info SET avatar=:avatar WHERE username=:username"),
                {"avatar": avatar, "username": session["username"]}
            )
            db.commit()

            flash("Avatar Changed!")
            return redirect("/settings")

        # Update social media links
        else:
            facebook = request.form.get("facebook")
            twitter = request.form.get("twitter")
            instagram = request.form.get("instagram")

            db.execute(
                text("UPDATE user_info SET facebook=:facebook, twitter=:twitter, instagram=:instagram WHERE username=:username"),
                {"facebook": facebook, "twitter": twitter, "instagram": instagram, "username": session["username"]}
            )
            db.commit()

            flash("Social Media Updated!")
            return redirect("/settings")

    # If GET request, render the settings template
    else:
        # You might want to fetch existing user data to pre-fill fields, if needed
        user_info = db.execute(
            text("SELECT * FROM user_info WHERE username=:username"),
            {"username": session["username"]}
        ).mappings().fetchone()

        return render_template("settings.html", user_info=user_info)


@socketio.on("send message")
def send_msg(msg, timestamp, recipient, date):
    # Analyze the message content for harmful attributes
    attribute = checkScore(msg)

    if attribute:
        chat = session['friend']
        warning_messages = {
            "SEVERE_TOXICITY": "Your message contains potentially harmful or toxic content. Please re-think your message and try again in one minute.",
            "IDENTITY_ATTACK": "Your message is potentially an attack on someone's identity. Please re-think your message and try again in one minute.",
            "THREAT": "Your message is potentially a threat to someone's wellbeing. Please re-think your message and try again in one minute.",
            "INSULT": "Your message is potentially offensive or insulting. Please re-think your message and try again in one minute.",
            "SEXUALLY_EXPLICIT": "Your message contains potentially sexually explicit content. Please re-think your message and try again in one minute."
        }

        # Insert the harmful attribute into the database
        insert_attribute(attribute.lower())

        # Emit a warning message to the sender
        emit('warning message', {'msg': warning_messages.get(attribute)}, chat=chat)

    else:
        # Sentiment analysis of the message
        sentiment = checkSentiment(msg)
        room = session.get("chat_id")

        # Fetch the friend's user ID
        friend_data = db.execute(
            text("SELECT id FROM users WHERE username=:username"),
            {"username": session['friend']}
        ).mappings().fetchone()

        if not friend_data:
            emit('warning message', {'msg': 'Error: Friend not found.'}, room=room)
            return

        friend_id = friend_data['id']

        # Fetch the conversation ID
        convo_data = db.execute(
            text("SELECT chat_id FROM chat_ids WHERE (p1_id=:p1_id AND p2_id=:p2_id) OR (p1_id=:p2_id AND p2_id=:p1_id)"),
            {"p1_id": session["user_id"], "p2_id": friend_id}
        ).mappings().fetchone()

        if not convo_data:
            emit('warning message', {'msg': 'Error: Conversation not found.'}, room=room)
            return

        convo_id = convo_data['chat_id']

        # Insert the message into the database
        print(timestamp, type(timestamp))
        print(date, type(date))
        db.execute(
            text("INSERT INTO messages (conversation_id, sender_id, reciever_id, time, message, sentiment) "
                 "VALUES (:conversation_id, :sender_id, :reciever_id, :time, :message, :sentiment)"),
            {
                "conversation_id": convo_id,
                "sender_id": session["user_id"],
                "reciever_id": friend_id,
                "time": date,
                "message": msg,
                "sentiment": sentiment,
            }
        )
        db.commit()

        # Emit the message to the room
        emit('announce message', {
            'timestamp': timestamp,
            'msg': msg,
            'recipient': recipient
        }, room=room)


@app.route("/dashboard")
@login_required
def dashboard():

    # Calculate the last 7 days including today
    dates = [(datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]

    # Fetch content and sentiment data for the last 7 days
    attributes = db.execute(
        text("SELECT * FROM attributes WHERE date>=:date AND user_id=:user_id"),
        {"date": dates[0], "user_id": session['user_id']}
    ).mappings().fetchall()

    msg_sentiments = db.execute(
        text("SELECT time, sentiment FROM messages WHERE time >= :time AND sender_id = :user_id"),
        {"time": dates[0], "user_id": session['user_id']}
    ).mappings().fetchall()

    channel_sentiments = db.execute(
        text("SELECT time, sentiment FROM channel_messages WHERE time >= :time AND sender = :user_id"),
        {"time": dates[0], "user_id": session['user_id']}
    ).mappings().fetchall()

    sentiments = msg_sentiments + channel_sentiments

    total_channel_msgs = db.execute(
        text("SELECT time FROM channel_messages WHERE sender = :user_id AND time >= :time"),
        {"user_id": session['user_id'], "time": dates[0]}
    ).mappings().fetchall()

    total_chat_msgs = db.execute(
        text("SELECT time FROM messages WHERE sender_id = :user_id AND time >= :time"),
        {"user_id": session['user_id'], "time": dates[0]}
    ).mappings().fetchall()

    total_msgs = total_channel_msgs + total_chat_msgs

    # Initialize day data for each of the 7 days
    days = [{
        "atr_total": 0,
        "total": 0,
        "sentiment": {"positive": 0, "negative": 0, "neutral": 0}
    } for _ in range(7)]

    # Breakdown for harmful messages
    breakdown = {'toxic': 0, 'identity': 0, 'threat': 0, 'sexual': 0, 'insult': 0}

    # Process attributes data
    for attribute in attributes:
        formatted_date = attribute['date'].strftime('%Y-%m-%d')
        if formatted_date in dates:
            index = dates.index(formatted_date)
            days[index]['atr_total'] += 1
            breakdown[attribute['attribute']] += 1

    # Process sentiment data
    for sentiment in sentiments:
        formatted_date = sentiment['time'].strftime('%Y-%m-%d')
        if formatted_date in dates:
            index = dates.index(formatted_date)
            days[index]['sentiment'][sentiment['sentiment']] += 1

    # Count total messages per day
    for msg in total_msgs:
        formatted_date = msg['time'].strftime('%Y-%m-%d')
        if formatted_date in dates:
            index = dates.index(formatted_date)
            days[index]['total'] += 1

    # Map days to the respective day1, day2, etc.
    day1, day2, day3, day4, day5, day6, day7 = days

    return render_template('dashboard.html', day1=day1, day2=day2, day3=day3, day4=day4, day5=day5, day6=day6, day7=day7, breakdown=breakdown, dates=dates)


@socketio.on("channel message")
def channel_msg(msg, timestamp, sender):
    # Check if the message contains harmful attributes
    attribute = checkScore(msg)

    if attribute:
        warning_messages = {
            "SEVERE_TOXICITY": "Your message contains potentially harmful or toxic content. Please re-think your message and try again in one minute.",
            "IDENTITY_ATTACK": "Your message is potentially an attack on someone's identity. Please re-think your message and try again in one minute.",
            "THREAT": "Your message is potentially a threat to someone's wellbeing. Please re-think your message and try again in one minute.",
            "INSULT": "Your message is potentially offensive or insulting. Please re-think your message and try again in one minute.",
            "SEXUALLY_EXPLICIT": "Your message contains potentially sexually explicit content. Please re-think your message and try again in one minute."
        }

        # Insert the harmful attribute into the database
        insert_attribute(attribute.lower())

        # Emit a warning message to the sender
        emit('warning message', {'msg': warning_messages.get(attribute)}, room=session.get("channel_id"))

    else:
        # Perform sentiment analysis on the message
        sentiment = checkSentiment(msg)

        # Retrieve the room (channel) ID
        room = session.get("channel_id")

        # Fetch sender's ID using their username
        sender_data = db.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": sender}
        ).mappings().fetchone()

        if not sender_data:
            emit('warning message', {'msg': 'Error: Sender not found.'}, room=room)
            return

        sender_id = sender_data["id"]

        # Insert the message into the channel_messages table
        print(timestamp, type(timestamp))
        db.execute(
            text("INSERT INTO channel_messages (channel_id, message, time, sender, sender_name, sentiment) "
                 "VALUES (:channel_id, :message, :time, :sender, :sender_name, :sentiment)"),
            {
                "channel_id": session["channel_id"],
                "message": msg,
                "time": timestamp,
                "sender": sender_id,
                "sender_name": sender,
                "sentiment": sentiment,
            }
        )
        db.commit()

        # Emit the message to the channel
        emit('announce channel_msg', {
            'timestamp': timestamp,
            'msg': msg,
            'sender': sender
        }, room=room)



@socketio.on("joined chat") 
def join_chat():
    room = session.get("chat_id")
    if room:
        join_room(room)
        emit('status', {'msg': f'{session["username"]} has joined the chat.'}, room=room)
    else:
        emit('status', {'msg': 'Error: Chat ID not found.'})


@socketio.on("joined channel")
def join_channel():
    room = session.get("channel_id")
    if room:
        join_room(room)
        emit('status', {'msg': f'{session["username"]} has joined the channel.'}, room=room)
    else:
        emit('status', {'msg': 'Error: Channel ID not found.'})


@socketio.on("left")
def left():
    room = session.get("channel_id")
    if room:
        leave_room(room)
        emit('status', {'msg': f'{session["username"]} has left the channel.'}, room=room)
    else:
        emit('status', {'msg': 'Error: Channel ID not found.'})


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.remove()


# function to return list of friends   
def friends(user_id):

    friends = db.execute(text("SELECT users.username FROM friendships \
        JOIN users ON users.id = friendships.person_id1 \
        WHERE friendships.person_id2=:user_id \
        UNION SELECT users.username FROM friendships \
        JOIN users ON users.id = friendships.person_id2\
        WHERE friendships.person_id1=:user_id "),
        {"user_id":user_id, "user_id":user_id, "user_id":user_id}).mappings().fetchall()

    return friends


def checkScore(comment):
    data_dict = {
        'comment': {'text': comment},
        'languages': ['en'],
        'requestedAttributes': {
            'SEVERE_TOXICITY': {},
            'IDENTITY_ATTACK': {},
            'THREAT': {},
            'INSULT': {},
            'SEXUALLY_EXPLICIT': {}
        }
    }

    try:
        response = requests.post(url=url_perspective, data=json.dumps(data_dict))
        response.raise_for_status()  # Raise an exception for HTTP errors
        scores = response.json()  # Parse JSON response

        # Get the attribute with the highest score
        highest_attribute = max(
            scores["attributeScores"].items(),
            key=lambda item: item[1]["summaryScore"]["value"]
        )

        score = highest_attribute[1]['summaryScore']['value']

        print("attribute score: ", score)

        # If the score is higher than 0.85, return the attribute
        if score > 0.60:
            return highest_attribute[0]
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error checking message score: {e}")
        return None



def insert_attribute(attribute):
    user_id = session['user_id']
    db.execute(text('INSERT INTO attributes (user_id, attribute, date) VALUES (:user_id, :attribute, :date)'),
            {'user_id': user_id, 'attribute': attribute, "date": datetime.now()})
    db.commit()


def checkSentiment(msg):
    data_dict = {
        "document": {
            "type": "PLAIN_TEXT",
            "content": msg
        },
        "encodingType": "UTF8"
    }

    try:
        response = requests.post(url=url_nlp, data=json.dumps(data_dict))
        response.raise_for_status()  # Raise an exception for HTTP errors
        sentiment_data = response.json()  # Parse the JSON response

        score = sentiment_data.get('documentSentiment', {}).get('score', 0)

        print(score)

        # Determine the sentiment category based on the score
        if score > 0.5:
            return 'positive'
        elif score < -0.25:
            return 'negative'
        else:
            return 'neutral'

    except requests.exceptions.RequestException as e:
        print(f"Error checking sentiment: {e}")
        return 'neutral'  # Return neutral in case of an error


def get_avatars():
    results = db.execute(text("SELECT username, avatar FROM user_info")).mappings().fetchall()

    # Create a dictionary of avatars with usernames as keys
    avatars = {row['username']: row['avatar'] for row in results}
    
    return avatars


if __name__ == '__main__':
    socketio.run(app, debug=True)

