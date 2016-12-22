from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from functools import wraps
import config
from werkzeug.security import generate_password_hash, check_password_hash
from steamtracker import playtime, minutes_played_this_session, reset_user
import os
import datetime

# Application Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = config.secret_key
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'tracker.db')

# Database configuration
db = SQLAlchemy(app)


class Users(db.Model):

    __tablename = 'Users'

    db_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))

    def __init__(self, email, password):
        self.email = email
        self.set_password(password)

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)


class SteamTrackers(db.Model):

    __tablename__ = 'SteamTrackers'

    steam_id = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.db_id'))
    users = db.relationship('Users', backref=db.backref('steamtrackers', lazy='dynamic'))
    start_playtime = db.Column(db.Integer)
    start_date = db.Column(db.DATE, default=datetime.datetime.now())
    time_limit = db.Column(db.Integer)
    current_playtime = db.Column(db.Integer)
    notified = db.Column(db.Boolean, default=False)


# Functions

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if str(session.get('logged_in')) == 'True':
            return f(*args, **kwargs)
        else:
            flash("You must be logged in to use this feature.")
            return redirect(url_for('homepage'))

    return wrap


# Routing
@app.route('/')
def homepage():
    if str(session.get('logged_in')) == 'True':
        return redirect(url_for("track"))
    return render_template("homepage.html")


@app.route('/login/', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        query = Users.query.filter_by(email=request.form['email']).first()
        if query and query.check_password(request.form['password']):
            session['logged_in'] = True
            session['user'] = query.db_id
            flash('Login Successful')
            return redirect('/')

        else:
            flash("Login Failed")
            return render_template("login.html")

    return render_template("login.html")


@app.route('/register/',  methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form['password'] == request.form['confirm']:
            new_user = Users(email=request.form['email'], password=request.form['password'])
            steam_id = request.form['Steam_id']
            cur_playtime = playtime(steam_id)
            db.session.add(new_user)
            db.session.commit()
            user = Users.query.filter_by(email=request.form['email']).first()
            new_settings = SteamTrackers(steam_id=steam_id, user_id=user.db_id,
                                         start_date=datetime.datetime.now(), time_limit=request.form['Steam_limit'],
                                         start_playtime=cur_playtime, current_playtime=cur_playtime)
            db.session.add(new_settings)
            db.session.commit()
            flash('Register Successful!')
            return redirect('/login/')
        else:
            flash('Passwords do not match!')

    return render_template('register.html')


@app.route('/logout/', methods=["GET", "POST"])
@login_required
def logout():
    session.clear()
    return redirect("/")


@app.route('/settings/', methods=["GET", "POST"])
@login_required
def setting():
    if request.method == "POST":
        user = SteamTrackers.query.filter_by(user_id=session['user']).first()
        if str(request.form['Steam_id']):
            user.steam_id = request.form['Steam_id']
        if request.form['Steam_limit']:
            user.time_limit = request.form['Steam_limit']
        db.session.commit()
        flash('Notification Times Updated')
        return redirect(url_for('homepage'))
    return render_template('settings.html', applications=['Steam'])


@app.route("/track/")
@login_required
def track():
    user = SteamTrackers.query.filter_by(user_id=session['user']).first()
    updated_playtime = minutes_played_this_session(user)
    return render_template("track.html", playtime=round(updated_playtime / 60, 2),
                           time_left=(user.time_limit * 60 - updated_playtime) / 60)


@app.route("/reset/", methods=["GET", "POST"])
@login_required
def reset():
    user = SteamTrackers.query.filter_by(user_id=session['user']).first()
    reset_user(user)
    db.session.commit()
    return redirect(url_for('homepage'))


if __name__ == '__main__':

    app.run(debug=True)