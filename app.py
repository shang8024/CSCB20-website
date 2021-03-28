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

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method=='POST':
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
                'username': user['username'],
                'name': [user['first_name'],user['last_name']],
                'type': user['type']
            }
            return redirect(url_for('home'))
        else:
            error = 'Invalid password'
    elif 'user' in session:
        return redirect(url_for('home'))
    return render_template('index.html',error=error)


@app.route('/signup',methods=['GET', 'POST'])
def signup():
    db = get_db()
    db.row_factory = make_dicts
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'first_name' in request.form and 'last_name' in request.form and 'utorid' in request.form and 'class' in request.form:
        curr_username = request.form['username']
        curr_f_name = request.form['first_name']
        curr_l_name = request.form['last_name']
        curr_utorid = request.form['utorid'] #currently set to email address
        curr_class = request.form['class']
        curr_ps = request.form['password']

        sql_username = query_db('select username from Users where username=?', [curr_username], one=True)
        #sql_uid = query_db('select username from Users where utorid=?', [curr_utorid], one=True)
        if(sql_username == None): #and #sql_uid == None):
            #insert our new User info:
            print(sql_username)
            #print(sql_uid)
            data = [curr_username, curr_f_name, curr_l_name, curr_ps, curr_utorid, curr_class]
            db.execute('INSERT INTO Users (username,first_name,last_name,password,email,type) VALUES (?,?,?,?,?,?)', (*data,))#(curr_username,curr_f_name,curr_l_name,curr_ps,curr_class))
            db.commit()
            db.close()
            return render_template('login.html')
    else:
        msg = 'Please fill out the form!'
        render_template('signup.html')




@app.route("/grade")
def grade():
    if not 'user' in session:
        return render_template('index.html')
    db=get_db()
    db.row_factory = make_dicts
    grades = get_grade_table()
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
    db.close() 
    return redirect(url_for('grade'))

@app.route("/grading", methods=['POST'])
def grading():
    error=None
    student=request.form['student']
    user=session['user']['username']
    event=request.form['event']
    grade=request.form['grade']
    db=get_db()
    db.row_factory = make_dicts
    if (not grade) or (not student) or (not event):
        error = "None of grade,username and type can be empty."
        return render_template('grade.html',user=session['user'],grade=get_grade_table(),error=error)
    if not query_db("select * from Takes where username='%s' and cid in (select cid from Takes where username='%s')" % (student,user)):
        error = "The student is not in your class."
    return render_template('grade.html',user=session['user'],grade=get_grade_table(),error=error)

@app.route("/remark-sort")
def remark_sort():
    db=get_db()
    db.row_factory = make_dicts
    grades=[]
    for grade in query_db("select distinct username, grade, remark, ename,request from Grades natural join Takes natural join Events where remark=1 and cid in (select cid from Takes where username='%s')" % (session['user']['username'])):
        grades.append(grade)
    db.close()
    return render_template('grade.html',user=session['user'],grade=grades)

@app.route("/setting")
def setting():
    if not 'user' in session:
        return render_template('index.html')
    return render_template('grade.html',user=session['user'])
@app.route("/feedback")
def feedback():
    if not 'user' in session:
        return render_template('index.html')
    return render_template('grade.html',user=session['user'])

@app.route('/labs')
def labs():
    if not 'user' in session:
        return render_template('index.html')
    return render_template('labs.html',user=session['user'])

@app.route('/lectures')
def lectures():
    if not 'user' in session:
        return render_template('index.html')
    return render_template('lectures.html',user=session['user'])

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)
