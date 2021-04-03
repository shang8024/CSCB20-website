# required imports
import sqlite3
from flask import Flask
from flask import Flask, jsonify,render_template, request, g, flash, redirect,session, url_for,abort
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
    if session['user']['type']:
        # query of getting all the students' grades of the instroctor's classes
        query = "select distinct username, grade, remark, ename,request from Grades natural join Takes where cid in (select cid from Takes where username='%s')" % (session['user']['username'])
    else:
        # query of getting all the grades of the student
        query = "select * from Grades where username='%s'" % (session['user']['username'])
    for grade in query_db(query):
        grades.append(grade)
    db.close()
    return grades

def get_student_table():
    db=get_db()
    db.row_factory = make_dicts
    students=[]
    for i in query_db("select distinct username from Takes natural join Users where type=0 and cid in (select cid from Takes where username='%s')" % (session['user']['username'])):
        students.append(i)
    return students
def get_event_table():
    db=get_db()
    db.row_factory = make_dicts
    events=[]
    for j in query_db('select * from Events'):
        events.append(j)
    return events

def grade_changes(student,event,grade):
    user=session['user']['username']
    db=get_db()
    db.row_factory = make_dicts
    grades=query_db("select * from Grades where username='%s' and ename='%s'" % (student,event),one=True)
    if not grades:
        # grade(student,event) does not exist
        # insert event to Events(ename) if not exist
        query_db("insert into Events(ename) select '%s' where not exists(select 1 from Events where ename='%s')" % (event,event))
        db.commit()
        # insert value(student,event,grade,0) into Events(username,ename,grade,remark)
        query_db("insert into Grades(username,ename,grade,remark) values('%s','%s',%s,0)" % (student,event,grade)) 
    else:
        # grade(student,event) exist, update existing row.
        if grades['remark'] == 1:
            # if the student is requesting a remark for that grade, set the remark status to 'remarked'
            grades['remark'] = -1
        query_db("update Grades set remark=%d, grade=%s where ename='%s' and username='%s'" % (grades['remark'],grade,event,student))
    db.commit()


# tells Flask that "this" is the current running app
app = Flask(__name__)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
    
@app.route('/')
def home():
    if not 'user' in session:
        return render_template('login.html',)
    else:
        return render_template('index.html',user=session['user'])

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
            data= {
                'first_name': user['first_name'],
                'last_name': user['last_name']
            }
            session['user'] = {
                'username': user['username'],
                'name': data,
                'type': user['type'],
                'email': user['email']
            }
            return redirect(url_for('home'))
        else:
            error = 'Invalid password'
    elif 'user' in session:
        return redirect(url_for('home'))
    return render_template('login.html',error=error)

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect(url_for('home'))

@app.route('/signup',methods=['GET', 'POST'])
def signup():
    db = get_db()
    db.row_factory = make_dicts
    error = None
    if('return' in request.form):
        return render_template('login.html')
    classes=[]
    for item in query_db('select * from Classes'):
        classes.append(item)
    if(error == None and request.method != 'POST'):
        return render_template('signup.html',class_list=classes)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'first_name' in request.form and 'last_name' in request.form and 'type' in request.form and 'email' in request.form and 'check' in request.form:
        curr_username = request.form['username']
        curr_f_name = request.form['first_name']
        curr_l_name = request.form['last_name']
        curr_email = request.form['email']
        curr_type = request.form['type']
        curr_ps = request.form['password']
        curr_class = request.form.getlist('check')
        if(query_db('select username from Users where username=?', [curr_username], one=True) == None): #and #sql_uid == None):
            #insert our new User info:
            #print(sql_uid)
            query_db('INSERT INTO Users (username,first_name,last_name,password,email,type) VALUES (?,?,?,?,?,?)',[curr_username, curr_f_name, curr_l_name, curr_ps, curr_email, curr_type])
            for item in curr_class:
                query_db('INSERT INTO Takes(username,cid) values(?,?)',[curr_username,item])
            db.commit()
            db.close()
            error = "Register successful!"
            return render_template('signup.html',class_list=classes, error = error)
        else:
            error = 'Username exists!!!!! Try again!'
            return render_template('signup.html',class_list=classes, error = error)
    else:
        error = 'Please Fill-in EVERY field to register'
        return render_template('signup.html',class_list=classes,error = error)

@app.route("/grade",methods=['GET','POST'])
def grade():
    if not 'user' in session:
        return redirect(url_for('home'))
    db=get_db()
    db.row_factory = make_dicts
    if session['user']['type']:
        students=get_student_table()
        events=get_event_table()
        grades = get_grade_table()
        return render_template('grade_i.html',event=events,user=session['user'],grade=grades,student=students)
    else:
        grades = get_grade_table()
        return render_template('grade_s.html',user=session['user'],grade=grades)

@app.route("/search-grade",methods=['GET','POST'])
def search_grade():
    if not 'user' in session:
        return redirect(url_for('home'))
    if request.method == 'GET':
        db=get_db()
        db.row_factory = make_dicts
        students=get_student_table()
        events=get_event_table()
        student=request.args.get('search-student')
        event=request.args.get('search-event')
        grade=request.args.get('search-grade')
        query="select distinct username, grade, remark, ename,request from Grades natural join Takes natural join Events where ename='%s' and cid in (select cid from Takes where username='%s')" % (event,session['user']['username'])
        if grade:
            query += " and grade=%s" % (grade)
        if student:
            query += " and username='%s'" % (student)
        grades=[]
        for i in query_db(query):
            grades.append(i)
        db.close()
        return render_template('grade_i.html',event=events,user=session['user'],grade=grades,student=students)
    else:
        return redirect(url_for('grade'))

@app.route("/grade-remark",methods=['GET','POST'])
def request_remark():
    if not 'user' in session:
        return redirect(url_for('home'))
    else:
        db=get_db()
        db.row_factory = make_dicts
        remark_req = request.form['remark_request']
        remark_eve = request.form['remark_event']
        user=session['user']['username']
        # if student request a remark, set remark status as 1
        query_db("update Grades set remark=?, request=? where username=? and ename=?",[1,remark_req,user,remark_eve])
        db.commit()
        db.close()
    return redirect(url_for('grade'))

@app.route("/grading",methods=['GET','POST'])
def grading():
    if not 'user' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        # if instructor submit temp changes
        # update evey grade change in list received from java
        db=get_db()
        db.row_factory = make_dicts
        changes = request.json['changes']
        for item in changes:
            grade_changes(item['username'],item['ename'],item['grade'])
        db.commit()
        db.close()
    #No, it won't actually rerender the page, since it is called by java, just for safety thought
    return redirect(url_for('grade'))

@app.route("/deleting",methods=['GET','POST'])
def deleting():
    if not 'user' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        db=get_db()
        db.row_factory = make_dicts
        username=request.json['username']
        ename=request.json['ename']
        query_db('delete from Grades where username=? and ename=?',[username,ename])
        db.commit()
        db.close()
    #No, it won't actually rerender the page, since it is called by java,just for safety thought
    return redirect(url_for('grade'))

@app.route("/remark-sort")
def remark_sort():
    if not 'user' in session:
        return redirect(url_for('home'))
    db=get_db()
    db.row_factory = make_dicts
    grades=[]
    for grade in query_db("select distinct username, grade, remark, ename,request from Grades natural join Takes where remark=1 and cid in (select cid from Takes where username='%s')" % (session['user']['username'])):
        grades.append(grade)
    students=get_student_table()
    events=get_event_table()
    db.close()
    return render_template('grade_i.html',user=session['user'],grade=grades,student=students,event=events)

@app.route('/feedback',methods=['GET', 'POST'])
def feedback():
    if not 'user' in session:
        return redirect(url_for('home'))
    db = get_db()
    db.row_factory = make_dicts
    name=session['user']['username']
    if session['user']['type']:
        feedbacks=[]
        for item in query_db('select qname,ans from Feedback natural join Questions where username=?',[name]):
            feedbacks.append(item)
        db.close
        #return feedbacks.__str__()
        return render_template('feedback_i.html',user=session['user'],feedback = feedbacks)
    else:
        instructors=[]
        submit = ''
        for instructor in query_db('SELECT* FROM Users WHERE type == 1'):
            instructors.append(instructor)
        if request.method=='POST':
            submit = 'Please do not submit everything empty!'
            if request.form['q1'] != '':
                insert_data = [request.form['iuser'],request.form['q1']]
                db.execute('INSERT INTO Feedback (username,qid,ans) VALUES (?,1,?)',(*insert_data,))
                submit = 'Submitted Successfully!'
            if request.form['q2'] != '':
                insert_data = [request.form['iuser'],request.form['q2']]
                db.execute('INSERT INTO Feedback (username,qid,ans) VALUES (?,2,?)',(*insert_data,))
                submit = 'Submitted Successfully!'
            if request.form['q3'] != '':
                insert_data = [request.form['iuser'],request.form['q3']]
                db.execute('INSERT INTO Feedback (username,qid,ans) VALUES (?,3,?)',(*insert_data,))
                submit = 'Submitted Successfully!'
            if request.form['q4'] != '':
                insert_data = [request.form['iuser'],request.form['q4']]
                db.execute('INSERT INTO Feedback (username,qid,ans) VALUES (?,4,?)',(*insert_data,))
                submit = 'Submitted Successfully!'
        db.commit()
        db.close
        #return instructors.__str__()
        return render_template('feedback_s.html',user=session['user'],instructor = instructors,submit = submit)

@app.route('/setting',methods=['GET', 'POST'])
def setting():
    if not 'user' in session:
        return redirect(url_for('home'))
    error = ['','','','']
    db = get_db()
    db.row_factory = make_dicts
    username=session['user']['username']
    if request.method == 'POST':
        #return request.form.__str__()
        if 'password2' in request.form:
            error[0] = 'The two password are inconsistent!'
            if request.form['password1'] == request.form['password2']:
                db.execute('UPDATE Users SET password = ? WHERE username = ?',(*[request.form['password2'], username],))
                error[0] = 'Reset Successfully!'
        if 'first_name' in request.form:
            session['user']['name']['first_name'] = request.form['first_name']
            db.execute('UPDATE Users SET first_name = ? WHERE username = ?',(*[request.form['first_name'], username],))
            error[1] = 'Reset Successfully!'
        if 'last_name' in request.form:
            session['user']['name']['last_name'] = request.form['last_name']
            db.execute('UPDATE Users SET last_name = ? WHERE username = ?',(*[request.form['last_name'], username],))
            error[2] = 'Reset Successfully!'
        if 'email' in request.form:
            if request.form['email'] == 'None' or request.form['email'] == '':
                session['user']['email'] = 'None'
                db.execute('UPDATE Users SET email = NULL WHERE username = ?',(*[username],))
                error[3] = 'Email Deleted Successfully!'
            else:
                session['user']['email'] = request.form['email']
                db.execute('UPDATE Users SET email = ? WHERE username = ?',(*[request.form['email'], username],))
                error[3] = 'Reset Successfully!'
    db.commit()
    db.close
    return render_template('setting.html',user=session['user'],error = error)

@app.route('/labs')
def labs():
    if not 'user' in session:
        return redirect(url_for('home'))
    return render_template('labs.html',user=session['user'])

@app.route('/lectures')
def lectures():
    if not 'user' in session:
        return redirect(url_for('home'))
    return render_template('lectures.html',user=session['user'])

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True)
