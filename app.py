# required imports
import sqlite3
from flask import Flask
from flask import Flask, render_template, request, g, flash, redirect,session, url_for,abort
import os

DATABASE='./assignment3.db'

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
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_grade_table():
    db=get_db()
    db.row_factory = make_dicts
    grades=[]
    if(session['user']['type']):
        # query of getting all the students' grades of the instroctor's classes
        query = "select username, grade, remark, ename,request from Grades natural join Takes natural join Events where cid in (select cid from Takes where username='%s')" % (session['user']['username'])
    else:
        # query of getting all the grades of the student
        query = "select * from Grades natural join Events where username='%s'" % (session['user']['username'])
    for grade in query_db(query):
        grades.append(grade)
    db.close()
    return grades

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
        return render_template('home.html',user=session['user'])

@app.route('/login', methods=['POST'])
def login():
    error = None
    login_name = request.form['username']
    login_pass = request.form['password']
    db=get_db()
    db.row_factory = make_dicts
    user = query_db('select * from Users where username=?',[login_name],one=True)
    if user == None:
        error = 'Invalid username'
    elif login_pass == user['password']:
        session['logged_in'] = True
        session['user'] = {
            "username": user['username'],
            "name": [user['first_name'],user['last_name']],
            "type": user['type']
        }
        return redirect(url_for('home'))
    else:
        error = 'Invalid password'
    return render_template('index.html',error=error)

@app.route("/logout")
def logout():
    session['logged_in'] = False
    session.pop('user',None)
    return root()

@app.route("/grade")
def grade():
    grades=get_grade_table()
    return render_template('grade.html',user=session['user'],grade=grades)

@app.route("/grade-remark", methods=['POST'])
def request_remark():
    db=get_db()
    db.row_factory = make_dicts
    remark_req = request.form['remark_request']
    remark_eve = request.form['remark_event']
    query = "update Grades set remark=1, request='%s' where username='%s' and eid in (select eid from Events where ename='%s')" % (remark_req,session['user']['username'],remark_eve)
    query_db(query)
    db.commit()
    grades=get_grade_table()
    return render_template('grade.html',user=session['user'],grade=grades)

@app.route("/setting")
def setting():
    return render_template('grade.html',user=session['user'])
@app.route("/feedback")
def feedback():
    return render_template('grade.html',user=session['user'])
@app.route('/home')
def home():
    # some code here for updating course team
    return render_template('home.html',user=session['user'])

@app.route('/labs')
def labs():
    return render_template('labs.html',user=session['user'])

@app.route('/lectures')
def lectures():
    return render_template('lectures.html',user=session['user'])

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)