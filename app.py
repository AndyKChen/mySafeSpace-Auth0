import os
import uuid

from flask import Flask, session, flash, redirect, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import deque
from datetime import datetime, timedelta, date

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
# postgres://oobmeddlzlecss:3fe732ad03fae55f28fbe06f600c8b3d8464073e3a99385a0326f509fa9ed5bc@ec2-3-229-210-93.compute-1.amazonaws.com:5432/d4bk3mrofa9d8k
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



names = dict()


@app.route("/")
@login_required
def index():
    messages = dict()

    friend_list = friends(session["user_id"])

    user_info = db.execute("SELECT * FROM user_info WHERE username=:username", {"username":session["username"]}).fetchall()[0]

    for friend in friend_list:

        username = friend[0]
        
        
        friend_id = db.execute("SELECT id FROM users WHERE username=:username", {"username":username}).fetchone()[0]

        name = db.execute("SELECT first FROM users WHERE username=:username", {"username": friend[0]}).fetchone()[0]

        try:
            msg = db.execute("SELECT message FROM messages WHERE (sender=:sender AND reciever=:reciever) OR (sender=:reciever and reciever=:sender) ORDER BY date DESC", 
            {"sender":session["user_id"], "reciever":friend_id}).fetchone()[0]
        except TypeError:
            msg = "No chats yet!"

        messages.update({username:msg})
        names.update({friend[0]: name})

    avatars = get_avatars()

    
    return render_template("index.html", friends=friend_list, user_info=user_info, avatars=avatars, messages=messages)

@app.route("/chat/<friend>")
@login_required
def chat(friend):

    friend_list = friends(session["user_id"])
    p2_id = db.execute("SELECT id FROM users WHERE username=:username", {"username": friend}).fetchone()[0]

    session['friend'] = friend
    session['chat_id'] = db.execute("SELECT chat_id FROM chat_ids WHERE (p1_id=:p1_id AND p2_id=:p2_id) OR (p1_id=:p2_id AND p2_id=:p1_id)", 
        {"p1_id": session["user_id"], "p2_id":p2_id}).fetchone()[0]
 
    friend_id = db.execute("SELECT id FROM users WHERE username=:username", {"username":friend}).fetchone()[0]

    messages = db.execute("SELECT messages.sender, messages.reciever, messages.time, messages.message FROM messages \
        JOIN chat_ids ON chat_ids.chat_id = messages.conversation_id \
        WHERE p1_id=:p1_id AND p2_id=:p2_id",
        {"p1_id": session["user_id"], "p2_id": friend_id}).fetchall()
    
    avatars = get_avatars()

    

    
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
        checkUser = db.execute("SELECT * from users WHERE username=:username",
            {"username":username}).fetchone()

        checkEmail = db.execute("SELECT * from users WHERE email=:email",
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
        db.execute("INSERT INTO users (username, password, email, first, last) VALUES (:username, :password, :email, :first, :last)",
            {"username":username, "password":pw, "email":email, "first": first, "last":last})
        db.commit()

        # insert default user info into db
        db.execute("INSERT INTO user_info (username, avatar, facebook, twitter, instagram) VALUES (:username, :avatar, :facebook, :twitter, :instagram)", 
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

        checkUser = db.execute("SELECT * from users WHERE username=:username OR email=:username",
            {"username":username, "email":username}).fetchone()

        if not checkUser:
            flash("Username or Email does not exist.")
            return render_template("login.html")

        elif not sha256_crypt.verify(password, checkUser[3]):
            flash("Incorrect Password")
            return render_template("login.html")

        session["user_id"] = checkUser[0]
        session["username"] = checkUser[1]
        session["name"] = checkUser[4]

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
        
        # get user submitted info
        title = request.form.get("title")
        topic = request.form.get("topic")
        picture = request.form.get("picture")

        if picture == None:
            picture = "default"

        # create unique channel id
        id = uuid.uuid1()
        channel_id = id.hex

        db.execute("INSERT INTO channels (channel_id, title, topic, picture) VALUES (:channel_id, :title, :topic, :picture)", {"channel_id":channel_id, "title":title, "topic":topic,"picture":picture})
        db.commit()

        flash("Channel Created")
        return redirect("/create")


    return render_template("create.html")


@app.route("/friends", methods = ["GET", "POST"])
@login_required
def friends():

    username = session["username"]
    user_id = session["user_id"]

    # display friend list
    friend_list = friends(user_id)

    if request.method == "POST":
        
        # user input for friend to add
        friend = request.form.get("friend")

        # search for user id of friend in database
        try: 
            friend_id = db.execute("SELECT id FROM users WHERE username=:username", {"username":friend}).fetchone()[0]

            if not friend_id:
                flash("Sorry, this user does not exist.")
                return redirect("/friends")

            elif friend_id == session["user_id"]:
                flash("You cannot add yourself, silly!")
                return redirect("/friends")

        except TypeError:
            flash("Sorry, this user does not exist.")
            return redirect("/friends")


        # check if user is already friends
        existing = db.execute("SELECT * FROM friendships WHERE person_id1=:user_id AND person_id2=:friend_id", {"user_id": user_id, "friend_id": friend_id}).fetchone()

        if existing:
            flash("You are already friends with this person!")
            return redirect("/friends")

        # insert new friendship into db
        db.execute("INSERT INTO friendships (person_id1, person_id2, date) VALUES (:p1, :p2, :date)", 
            {"p1":user_id, "p2":friend_id, "date":datetime.date(datetime.now())})
        db.commit()
        
        # create unique conversation id
        id = uuid.uuid1()
        chat_id = id.hex

        # establish new 1on1 chat relationship 
        db.execute("INSERT INTO chat_ids (chat_id, p1_id, p2_id) VALUES (:chat_id, :p1_id, :p2_id)", {"chat_id":chat_id, "p1_id":user_id, "p2_id":friend_id})
        db.commit()

        db.execute("INSERT INTO chat_ids (chat_id, p1_id, p2_id) VALUES (:chat_id, :p1_id, :p2_id)", {"chat_id":chat_id, "p1_id":friend_id, "p2_id":user_id})
        db.commit()


        flash("Friend Added!")

        return redirect("/friends")
    
    if request.method == "GET":

        for friend in friend_list:
            name = db.execute("SELECT first FROM users WHERE username=:username", {"username": friend[0]}).fetchone()[0]
            names.update({friend[0]: name})
        
        avatars = get_avatars()

        return render_template("friends.html", friends=friend_list, avatars=avatars, names=names)


@app.route("/channels")
@login_required
def channels():

    # get user social media and avatar
    user_info = db.execute("SELECT * FROM user_info WHERE username=:username", {"username":session["username"]}).fetchall()[0]

    # get channels
    channels = db.execute("SELECT * FROM channels").fetchall()

    return render_template("channels.html", user_info=user_info, channels=channels)

@app.route("/channel/<channel_id>")
@login_required
def chats(channel_id):

    # get channel information
    channels = db.execute("SELECT * FROM channels").fetchall()

    # get current channel information
    current_channel = db.execute("SELECT * FROM channels WHERE channel_id=:channel_id", {"channel_id": channel_id}).fetchone()

    # get user information
    user_info = db.execute("SELECT * FROM user_info WHERE username=:username", {"username":session["username"]}).fetchone()[0]

    # get channel messages
    messages = db.execute("SELECT * FROM channel_messages WHERE channel_id=:channel_id", {"channel_id": channel_id})

    session["channel_id"] = channel_id

    avatars = get_avatars()


    return render_template("channel_chat.html", channels=channels, avatars=avatars, user_info=user_info, messages=messages, current_channel=current_channel)

@app.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    
    if request.method == "POST":
        
        # check for avatar change
        if request.form.get("avatar"):
            avatar = request.form.get("avatar")

            db.execute("UPDATE user_info SET avatar=:avatar WHERE username=:username", {"avatar":avatar, "username":session["username"]})
            db.commit()
            
            flash("Avatar Changed!")
            return redirect("/settings")
        
        else:
            facebook = request.form.get("facebook")
            twitter = request.form.get("twitter")
            instagram = request.form.get("instagram")

            db.execute("UPDATE user_info SET facebook=:facebook, twitter=:twitter, instagram=:instagram WHERE username=:username", 
                {"facebook": facebook, "instagram":instagram,"twitter":twitter,"username":session["username"]})
            db.commit()

            flash("Social Media Updated!")
            return redirect("/settings")
  
    else:
        return render_template("settings.html")


@app.route("/dashboard")
@login_required
def dashboard():

    # FIND SEVEN DAYS INCLUDING TODAY'S DATE
    dates = [(datetime.today() - timedelta(days=6)).strftime('%Y-%m-%d'), 
            (datetime.today() - timedelta(days=5)).strftime('%Y-%m-%d'),
            (datetime.today() - timedelta(days=4)).strftime('%Y-%m-%d'),
            (datetime.today() - timedelta(days=3)).strftime('%Y-%m-%d'),
            (datetime.today() - timedelta(days=2)).strftime('%Y-%m-%d'),
            (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d'),
            (datetime.today()).strftime('%Y-%m-%d')]

    # CONTENT DATA
    attributes = db.execute("SELECT * FROM attributes WHERE date>=:date AND user_id=:user_id", {"date":dates[0], "user_id":session['user_id']}).fetchall()
    
    # SENTIMENT DATA
    msg_sentiments = db.execute("SELECT date, sentiment FROM messages WHERE date>=:date AND sender=:user_id", {"date":dates[0], "user_id" : session['user_id']}).fetchall()
    channel_sentiments = db.execute("SELECT date, sentiment FROM channel_messages WHERE date>=:date AND sender=:user_id", {"date":dates[0], "user_id" : session['user_id']}).fetchall()
    sentiments = msg_sentiments + channel_sentiments

    total_channel_msgs = db.execute("SELECT date FROM channel_messages WHERE sender=:user_id AND date>=:date", {"user_id": session['user_id'], "date":dates[0]}).fetchall()
    total_chat_msgs = db.execute("SELECT date FROM messages WHERE sender=:user_id AND date>=:date", {"user_id": session['user_id'], "date":dates[0]}).fetchall()
    total_msgs = total_channel_msgs + total_chat_msgs


    day1 = {"atr_total" : 0, "total": 0, "sentiment" : {"positive": 0, "negative" : 0, "neutral": 0}}
    day2 = {"atr_total" : 0, "total": 0, "sentiment" : {"positive": 0, "negative" : 0, "neutral": 0}}
    day3 = {"atr_total" : 0, "total": 0, "sentiment" : {"positive": 0, "negative" : 0, "neutral": 0}}
    day4 = {"atr_total" : 0, "total": 0, "sentiment" : {"positive": 0, "negative" : 0, "neutral": 0}}
    day5 = {"atr_total" : 0, "total": 0, "sentiment" : {"positive": 0, "negative" : 0, "neutral": 0}}
    day6 = {"atr_total" : 0, "total": 0, "sentiment" : {"positive": 0, "negative" : 0, "neutral": 0}}
    day7 = {"atr_total" : 0, "total": 0, "sentiment" : {"positive": 0, "negative" : 0, "neutral": 0}}

    breakdown = dict({
        'toxic': 0,
        'identity': 0,
        'threat': 0,
        'sexual': 0,
        'insult': 0
    })


    for attribute in attributes:
        if str(attribute[2]) == dates[0]:
            day1['atr_total'] += 1
        elif str(attribute[2]) == dates[1]:
            day2['atr_total']  += 1
        elif str(attribute[2]) == dates[2]:
            day3['atr_total']  += 1
        elif str(attribute[2]) == dates[3]:
            day4['atr_total']  += 1
        elif str(attribute[2]) == dates[4]:
            day5['atr_total']  += 1
        elif str(attribute[2]) == dates[5]:
            day6['atr_total']  += 1
        elif str(attribute[2]) == dates[6]:
            day7['atr_total']  += 1
            breakdown[attribute[1]] += 1
        
    for sentiment in sentiments:
        if str(sentiment[0]) == dates[0]:
            day1['sentiment'][sentiment[1]] += 1
        if str(sentiment[0]) == dates[1]:
            day2['sentiment'][sentiment[1]] += 1
        if str(sentiment[0]) == dates[2]:
            day3['sentiment'][sentiment[1]] += 1
        if str(sentiment[0]) == dates[3]:
            day4['sentiment'][sentiment[1]] += 1
        if str(sentiment[0]) == dates[4]:
            day5['sentiment'][sentiment[1]] += 1
        if str(sentiment[0]) == dates[5]:
            day6['sentiment'][sentiment[1]] += 1
        if str(sentiment[0]) == dates[6]:
            day7['sentiment'][sentiment[1]] += 1

    
    for msg in total_msgs:
        if str(msg[0]) == dates[0]:
            day1['total'] += 1
        if str(msg[0]) == dates[1]:
            day2['total'] += 1
        if str(msg[0]) == dates[2]:
            day3['total'] += 1
        if str(msg[0]) == dates[3]:
            day4['total'] += 1
        if str(msg[0]) == dates[4]:
            day5['total'] += 1
        if str(msg[0]) == dates[5]:
            day6['total'] += 1
        if str(msg[0]) == dates[6]:
            day7['total'] += 1
    

    return render_template('dashboard.html', day1 = day1, day2 = day2, day3 = day3, day4 = day4, day5 = day5, day6 = day6, day7=day7, breakdown=breakdown, dates=dates)


@socketio.on("send message")
def send_msg(msg, timestamp, recipient):

    attribute = checkScore(msg)

    if attribute != None:
        chat = session['friend']

        if attribute == "SEVERE_TOXICITY":
            insert_attribute("toxic")
            emit('warning message', {
                'msg' : 'Your message contains potentially harmful or toxic content. Please re-think your message and try again in one minute.'},
                chat=chat)
        
        elif attribute == "IDENTITY_ATTACK":
            insert_attribute("identity")
            emit('warning message', {
                'msg' : "Your message is potentially an attack on someone's identity. Please re-think your message and try again in one minute."},
                chat=chat)

        elif attribute == "THREAT":
            insert_attribute("threat")
            emit('warning message', {
                'msg' : "Your message is potentially a threat to someone's wellbeing. Please re-think your message and try again in one minute."},
                chat=chat)

        elif attribute == "INSULT":
            insert_attribute("insult")
            emit('warning message', {
                'msg' : "Your message is potentially offensive or insulting. Please re-think your message and try again in one minute."},
                chat=chat)

        elif attribute == "SEXUALLY_EXPLICIT":
            insert_attribute("sexual")
            emit('warning message', {
                'msg' : "Your message contains potentially sexually explicit content. Please re-think your message and try again in one minute."},
                chat=chat)
        
    else:
        sentiment = checkSentiment(msg)

        chat = session['friend']
        room = session.get("chat_id")

        friend_id = db.execute("SELECT id FROM users WHERE username=:username", {"username":chat}).fetchone()[0]

        convo_id = db.execute("SELECT chat_id FROM chat_ids WHERE p1_id=:p1_id AND p2_id=:p2_id", {"p1_id":session["user_id"], "p2_id":friend_id}).fetchone()[0]
    
        db.execute("INSERT INTO messages (conversation_id, sender, reciever, time, message, sentiment) VALUES (:conversation_id, :sender, :reciever, :time, :message, :sentiment)", 
            {"conversation_id": convo_id, "sender":session["user_id"], "reciever": friend_id, "time":timestamp, "message":msg, "sentiment": sentiment})

        db.commit()


        emit('announce message', {
            'timestamp': timestamp,
            'msg': msg,
            'recipient':recipient},
            room=room)

@socketio.on("channel message")
def channel_msg(msg, timestamp, sender):

    attribute = checkScore(msg)

    if attribute != None:
        chat = session['friend']

        if attribute == "SEVERE_TOXICITY":
            insert_attribute("toxic")
            emit('warning message', {
                'msg' : 'Your message contains potentially harmful or toxic content. Please re-think your message and try again in one minute.'},
                chat=chat)
        
        elif attribute == "IDENTITY_ATTACK":
            insert_attribute("identity")
            emit('warning message', {
                'msg' : "Your message is potentially an attack on someone's identity. Please re-think your message and try again in one minute."},
                chat=chat)

        elif attribute == "THREAT":
            insert_attribute("threat")
            emit('warning message', {
                'msg' : "Your message is potentially a threat to someone's wellbeing. Please re-think your message and try again in one minute."},
                chat=chat)

        elif attribute == "INSULT":
            insert_attribute("insult")
            emit('warning message', {
                'msg' : "Your message is potentially offensive or insulting. Please re-think your message and try again in one minute."},
                chat=chat)

        elif attribute == "SEXUALLY_EXPLICIT":
            insert_attribute("sexual")
            emit('warning message', {
                'msg' : "Your message contains potentially sexually explicit content. Please re-think your message and try again in one minute."},
                chat=chat)

    else:
        sentiment = checkSentiment(msg)

        room = session.get("channel_id")

        sender_id = db.execute("SELECT id FROM users WHERE username=:username", {"username":sender}).fetchone()[0]

        db.execute("INSERT into channel_messages (channel_id, message, timestamp, sender, sender_name, sentiment) VALUES (:channel_id, :message, :timestamp, :sender, :sender_name, :sentiment)", 
            {"channel_id": session["channel_id"], "message":msg, "timestamp": timestamp, "sender": sender_id, "sender_name":sender, "sentiment": sentiment})

        db.commit()

        emit('announce channel_msg', {
            'timestamp': timestamp,
            'msg': msg,
            'sender':sender},
            room=room)


@socketio.on("joined chat") 
def join_chat():

    room = session.get("chat_id")
    join_room(room)

@socketio.on("joined channel")
def join_channel():
    
    room = session.get("channel_id")
    join_room(room)

    emit('status', {
        'msg' : session['username'] + ' has joined.'},
        room=room)

@socketio.on("left")
def left():

    room = session.get("channel_id")

    leave_room(room)

    emit('status', {
        'msg' : session['username'] + ' has left.'},
        room=room)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.remove()

# function to return list of friends   
def friends(user_id):

    friends = db.execute("SELECT users.username FROM friendships \
        JOIN users ON users.id = friendships.person_id1 \
        WHERE friendships.person_id2=:user_id \
        UNION SELECT users.username FROM friendships \
        JOIN users ON users.id = friendships.person_id2\
        WHERE friendships.person_id1=:user_id ",
        {"user_id":user_id, "user_id":user_id, "user_id":user_id}).fetchall()

    return friends

# function to return attribute of potentially malicious message
def checkScore(comment):

    data_dict = {
        'comment' : {'text': comment},
        'languages' : ['en'],
        'requestedAttributes' : {'SEVERE_TOXICITY' : {}, 'IDENTITY_ATTACK' : {}, 'THREAT': {}, 'INSULT' : {}, 'SEXUALLY_EXPLICIT' : {}}

    }

    response = requests.post(url=url_perspective, data=json.dumps(data_dict)) 
    scores = json.loads(response.content) 


    highest_attribute = max(
        scores["attributeScores"].items(),
        key=lambda item: item[1]["summaryScore"]["value"],
    )


    score = highest_attribute[1]['summaryScore']['value']

    if score > 0.85:
        return highest_attribute[0]
    else:
        return None


def insert_attribute(attribute):
    user_id = session['user_id']
    db.execute('INSERT INTO attributes (user_id, attribute) VALUES (:user_id, :attribute)',
            {'user_id': user_id, 'attribute': attribute})
    db.commit()


def checkSentiment(msg):
    
    data_dict = {
        "document":{
        "type":"PLAIN_TEXT",
        "content":msg
        },
        "encodingType": "UTF8"
    }

    response = requests.post(url=url_nlp, data=json.dumps(data_dict)) 

    score = json.loads(response.content)

    score = score['documentSentiment']['score']

    print(score)

    if score > 0.5:
        return 'positive'
    elif score < -0.25:
        return 'negative'
    else:
        return 'neutral'


def get_avatars():
    results = db.execute("SELECT username, avatar FROM user_info").fetchall()
    
    avatars = {}

    for row in results:
        avatars.update({row[0] : row[1]})

    return avatars


if __name__ == '__main__':
    socketio.run(app, debug=True)




    


