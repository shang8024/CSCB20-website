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
        return render_template('index.html',)
    else:
        return render_template('home.html',type=session['type'],name=session['name'])

@app.route('/login', methods=['POST'])
def login():
    error = None
    user = request.form['username']
    if request.form['password'] == 'password' and user == 'admin':
        session['username'] = user
        session['name'] = user #记得改成firstname
        session['type'] = 0 #记得改成user type
        session['logged_in'] = True
        return redirect(url_for('home'))
    else:
        error = 'Invalid redentials'
    return render_template('index.html',error=error)

@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['username'] = None
    session['type'] = False
    session['name'] = None
    return root()
@app.route("/grade")
def grade():
    return render_template('grade.html',type=session['type'],name=session['name'])
@app.route("/setting")
def setting():
    return render_template('grade.html',type=session['type'],name=session['name'])
@app.route("/feedback")
def feedback():
    return render_template('grade.html',type=session['type'],name=session['name'])
@app.route('/home')
def home():
    # some code here for updating course team
    return render_template('home.html',type=session['type'],name=session['name'])

@app.route('/labs')
def labs():
    return render_template('labs.html',type=session['type'],name=session['name'])

@app.route('/lectures')
def lectures():
    return render_template('lectures.html',type=session['type'],name=session['name'])

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)