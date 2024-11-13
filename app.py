#!/usr/bin/env python  #step 1 import library
import json  # Step1 import libraries
import requests
from flask import Flask, render_template, request, redirect, flash, session, url_for
from datetime import datetime, date
from flask_wtf import FlaskForm
import sqlite3
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, SelectMultipleField, SelectField, widgets
from wtforms.fields.html5 import DateField # see https://stackoverflow.com/questions/26057710/datepickerwidget-with-flask-flask-admin-and-wtforms
from wtforms.validators import DataRequired, URL, Optional, InputRequired

# Step2 - create instance of Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'myverysectretkey'



class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class signupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class searchform(FlaskForm):
    searchkey = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Submit')



#connect to database
con = sqlite3.connect('foodtruck.db', check_same_thread=False)
con.row_factory = sqlite3.Row
cur = con.cursor()

@app.route('/', methods=['GET'])
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    req = requests.get("https://www.bnefoodtrucks.com.au/api/1/trucks")
    data = json.loads(req.content)
    for truck in data:
        cur.execute(""" INSERT OR REPLACE INTO trucks (truck_id, name, category, bio, avatarsrc, avataralt, cover_photosrc, cover_photoalt, website, facebook_url, instagram_handle, twitter_handle)
        values(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (truck.get('truck_id'), truck.get('name'), truck.get('category'), truck.get('bio'), truck.get('avatar:src'),
        truck.get('avatar:alt'), truck.get('cover_photo:src'), truck.get('cover_photo:alt'), truck.get('website'), truck.get('facebook_url'), truck.get('instagram_handle'), truck.get('twitter_handle'),))
        con.commit()

    form = searchform()
    if request.method == 'POST':
        if form.validate_on_submit():
            searchkey = form.searchkey.data
            sql=("""select *
                    from trucks
                    where name LIKE ?""")
            cur.execute(sql,('%'+searchkey+'%',))
            searchresult = cur.fetchall()
            return render_template('search.html', searchresult=searchresult)
            # return redirect(url_for('search', searchresult=searchresult))

    return render_template('home.html', data=data, form=form)

# @app.route('/search', methods=['GET'])
# def search():
#     return render_template('search.html')

@app.route('/sites', methods=['GET', 'POST'])
def sites():
    req = requests.get("https://www.bnefoodtrucks.com.au/api/1/sites")
    data = json.loads(req.content)
    for site in data:
        cur.execute(""" INSERT OR REPLACE INTO sites (site_id, title, description, street, suburb, postcode)
        values(?,?,?,?,?,?)""",
        (site.get('site_id'), site.get('title') ,site.get('description'), site.get('street'), site.get('suburb'), site.get('postcode')))
        con.commit()

    form = searchform()
    if request.method == 'POST':
        if form.validate_on_submit():
            searchkey = form.searchkey.data
            sql = ("""select *
                        from sites
                        where title LIKE ?""")
            cur.execute(sql, ('%' + searchkey + '%',))
            searchresult = cur.fetchall()
            return render_template('search1.html', searchresult=searchresult)

    return render_template('sites.html', data=data, form=form)

@app.route('/upcomingtrucks', methods=['GET'])
def upcomingtrucks():
    req = requests.get("https://www.bnefoodtrucks.com.au/api/1/bookings")
    data = json.loads(req.content)
    for booking in data:
        cur.execute(""" INSERT OR REPLACE INTO bookings (title, truck_id, site_id, start, finish)
        values(?,?,?,?,?)""",
        (booking.get('title'), booking.get('truck_id') ,booking.get('site_id'), booking.get('start'), booking.get('finish')))
        con.commit()

        sql = ("""select b.title, s.title, s.street, s.suburb, s.postcode, b.start, b.finish, t.truck_id
                from trucks t, sites s, bookings b
                where s.site_id = b.site_id and t.truck_id = b.truck_id""")
        cur.execute(sql)
        upcoming = cur.fetchall()


    return render_template('neartruck.html', data=data, upcoming=upcoming)

@app.route('/truck', methods=['GET'])
def order_details():
    if request.args.get('tid'):
        tid = int(request.args.get('tid'))
        userid = session['userid']
        sql = """ select * from trucks
        where truck_id = ?;
        """
        cur.execute(sql, (tid,))
        trucksocial = cur.fetchone()

        sql = """ select * from favourites
            where userid = ? 
            and truck_id = ?;
            """
        cur.execute(sql, (userid,tid))
        favconfirm = cur.fetchone()

    if request.args.get('fid'):
        fid = int(request.args.get('fid'))
        userid = session['userid']
        cur.execute("""INSERT INTO favourites(truck_id, userid)
                             values(?,?);
                             """, (fid,userid))
        con.commit()
        flash('Successfully added Truck to Favourites')

    if request.args.get('ufav'):
        ufav = int(request.args.get('ufav'))
        userid = int(session['userid'])
        sql = """DELETE FROM favourites
                where truck_id = ? and userid = ?;"""
        cur.execute(sql,(ufav,userid,))
        con.commit()
        flash('Successfully removed Truck from Favourites')
    return render_template('trucks.html', trucksocial = trucksocial, favconfirm = favconfirm, tid=tid)

@app.route('/favourites', methods=['GET'])
def favourites():
    userid = session['userid']
    sql = """ select t.name, t.category, t.bio, t.truck_id, t.website
        from trucks t, favourites f
        where t.truck_id = f.truck_id
        and f.userid = ?;
       """
    cur.execute(sql, (userid,))
    favourites = cur.fetchall()
    return render_template('favourites.html', favourites=favourites)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            un = form.username.data
            pw = form.password.data
            sql = """
                    select *
                    from users
                    where username = ?
                    and password = ?;"""

            cur.execute(sql,(un,pw))
            result = cur.fetchall()
            if len(result) == 1:
                session['userid'] = result[0][0]
                session['username'] = result[0][1]
                session['name'] = result[0][2]
                return redirect(url_for('index'))
            else:
                flash('Username or password incorrect, try again')


        else:
            flash("There is something missing!")
    return render_template('login.html', title='Login', form=form)

@app.route('/signup', methods=['GET','POST'])
def signup():
    form = signupForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            un = form.username.data
            n = form.name.data
            pw = form.password.data

            cur.execute("""INSERT INTO users(username, name, password)
                     values(?,?,?);
                     """, (un,n,pw,))
            flash('Successfully signed up')
            con.commit()
            return redirect(url_for('index'))
        else:
            flash("There is something missing!")
    return render_template('signup.html', title='signup', form=form)


@app.route('/logout')
def logout():
    if session['userid']:
    # clear out the session
        session['userid'] = None
        session['username'] = None
        session['name'] = None
        flash("You have successfully logged out")
        return redirect(url_for('index'))


if __name__ == '__main__':
    host = '127.0.0.1'
    # port = 8080
    app.run(debug=True)