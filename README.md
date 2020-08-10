<h1 align="center">
	<img src="static/favicon/android-chrome-192x192.png" alt="Andy Chen" width="50px"></a>
 mySafeSpace: Instant Messaging WebApp
</h1>

<h4 align="center">Messaging WebApp for a Safer and Closer Online Community</h4>

      
<p align="center">
  <a href="#about">About</a> •
  <a href="#usage">Usage</a> •
  <a href="#author">Author</a> •
  <a href="#contact">Contact</a> •
  <a href="#license">License</a>
</p>

---

## About

<table>
<tr>
<td>

  
**myChat** is an **instant messaging web-app** that promotes mental health and digital citizenship. Users simply register a new account that is secured with a 256-bit encryption algorithm.

**Try it here:** http://mysafespace.herokuapp.com/ <br>


Submission to Auth0 Hackathon for category of **connecitivity** 

## How it works

**Safer Environment:** Perspective API used to determine if a message contains potentially toxic, insulting, racially insensitive, threatening, or sexually explicit content in real-time. If such a message is detected, user is prompted with a warning and short timeout to re-think their message. 
<ul>
	<li>Combat effects of cyberbullying and harrassment</li>
	<li>Focus on mental health</li>
	<li>Improve conversations and community connection with more welcoming environment for all ages</li>
	<li>Grow as a digital citizen</li>
</ul>

**Data Analytics**: Message sentiment is also analyzed over time using machine learning and displayed in an **intuitive dashboard UI.** Weekly and daily breakdowns are available for both message sentiment and message content so users can gauge their mood and digital citizenship over time. 

It comes **filled** with **features** including a wide selection of cartoon avatars, the ability to add friends, create a social media profile, and create channels. The webapp is optimized for desktop and mobile devices


## Inspiration
With the rapid growth of the internet in recent years, has come greater connectivity between people all over the world. However, there is always the concern of digital safety when it comes to things like cyberbullying, harassment and predators online. 

As the internet begins to play a larger role in our lives, it has become a medium for us to express our feelings and personal life. Especially with COVID-19 and social distancing, there is a greater need for online connectivity. A goal of this project was to use technology to improve conversations and to better understand our feelings and emotions. 


## Tech Stack & What I Used
<ul>
<li>Framework: Flask</li>
<li>Languages: Python, Javascript, HTML/CSS/Jinja2, SQL</li>
<li>Messaging: Socket-IO</li>
<li>Database: Postgres </li>
<li>Deployment: Heroku</li>
<li>Framework: Flask</li>
<li>Machine Learning: NLTK, pandas, numpy, scikit-learn</li>
<li>API: Perspective API, Google Cloud</li>
</ul>

## How to use it
Simply visit mysafespace.herokuapp.com for live version

Mobile Users: Add to home screen to view in fullscreen. Note it is not yet properly optimized for mobile.

Since this is a prototype, if there are any bugs please contact me for fixes.

For local deployment:

```bash
# Clone repo
$ git clone https://github.com/AndyKChen/myChat.git

# Install all dependencies
$ pip install -r requirements.txt

# Setup database using a tool such as adminer and get the credentials

# Set Environment Variables
$ SET DATABASE_URL = "your database"
$ SET SECRET = "your secret key"
$ SET FLASK_APP = app.py
$ SET API_KEY = "api key from perspectiveAPI"

# Run
$ python app.py

# Go to 127.0.0.1:5000 on your web browser.
```

## Accomplishments that I'm proud of
<ul>
<li>Although it is a protoype, there are a wide range of basic features found in popular messaging platforms</li>
<li>Succesful usage of API to classify content of user messages</li>
<li>Timeout function and warning popup</li>
<li>Dashboard UI with data analytics of message sentiment and content</li>
<li>Machine learning model to detect early signs of depression and give user's useful resources related to mental health</li>
</ul>

## What's next for mySafeSpace
<ul>
<li>Security Features: Using Auth0 for two factor authentication. </li>
<li>Scaling up: As users increase, change deployment method to scale. </li>
<li>New Features: Create private invite-only groupchats, fix mobile UI, Gamerooms</li>

</ul>


## License

[![License: CC BY-NC-SA 4.0](https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-orange.svg?style=flat-square)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

- Copyright © AndyC
