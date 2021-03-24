# required imports
import sqlite3
from flask import Flask
from flask import Flask, render_template, request, g, flash, redirect,session, url_for,abort
import os

DATABSE='./assginment3.db'

def get_db():
    db=getattr(g,'_database',None)
    if db is None:
        db=g._database=sqlite3.connect(DATABASE)
    return db

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0],value)
                for idx,value in enumerate(row))

def query_db(query, args=(),one=False):
    cur = get_db().execute(query,args)
    rv = curfetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv
# tells Flask that "this" is the current running app
app = Flask(__name__)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    
@app.route('/')
def root():
    if not session.get('logged_in'):
        return render_template('index.html',error= "username ")
    else:
        return render_template('home.html')

@app.route('/login', methods=['POST'])
def do_admin_login():

    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True

    return root()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return root()

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/labs')
def labs():
    return render_template('labs.html')
    
@app.route('/lectures')
def lectures():
    return render_template('lectures.html')

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)