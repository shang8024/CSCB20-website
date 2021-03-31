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
    if(session['user']['type']):
        # query of getting all the students' grades of the instroctor's classes
        query = "select username, grade, remark, ename,request from Grades natural join Takes where cid in (select cid from Takes where username='%s')" % (session['user']['username'])
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
    for i in query_db("select username from Takes natural join Users where type=0 and cid in (select cid from Takes where username='%s')" % (session['user']['username'])):
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
        return render_template('index.html')
    #first time login!!!!
    if(error == None and request.method != 'POST'):
        return render_template('signup.html')
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'first_name' in request.form and 'last_name' in request.form and 'type' in request.form and 'email' in request.form and ('Lec01' in request.form or 'Lec02' in request.form or 'Lec03' in request.form):
        curr_username = request.form['username']
        curr_f_name = request.form['first_name']
        curr_l_name = request.form['last_name']
        curr_email = request.form['email']
        curr_type = request.form['type']
        curr_ps = request.form['password']
        #three classes
        curr_class1 = request.form.getlist('Lec01')
        curr_class2 = request.form.getlist('Lec02')
        curr_class3 = request.form.getlist('Lec03')
        sql_username = query_db('select username from Users where username=?', [curr_username], one=True)
        #sql_uid = query_db('select username from Users where utorid=?', [curr_utorid], one=True)
        if(sql_username == None): #and #sql_uid == None):
            #insert our new User info:
            #print(sql_uid)
            data = [curr_username, curr_f_name, curr_l_name, curr_ps, curr_email, curr_type]
            db.execute('INSERT INTO Users (username,first_name,last_name,password,email,type) VALUES (?,?,?,?,?,?)', (*data,))#(curr_username,curr_f_name,curr_l_name,curr_ps,curr_class))
            if(curr_class1):#if class 1 value is not empty:
                take_data_1 = [curr_username,curr_class1[0]]
                db.execute('INSERT INTO Takes (username,cid) VALUES (?,?)', (*take_data_1,))
            if(curr_class2):#if class 2 value is not empty:
                take_data_2 = [curr_username,curr_class2[0]]
                db.execute('INSERT INTO Takes (username,cid) VALUES (?,?)', (*take_data_2,))
            if(curr_class3):#if class 3 value is not empty:
                take_data_3 = [curr_username,curr_class3[0]]
                db.execute('INSERT INTO Takes (username,cid) VALUES (?,?)', (*take_data_3,))
            db.commit()
            db.close()
            error = "Register successful!"
            return render_template('signup.html', error = error)
        else:
            error = 'Username exists!!!!! Try again!'
            return render_template('signup.html', error = error)
    else:
        error = 'Please Fill-in EVERY field to register'
        return render_template('signup.html',error = error)

@app.route("/grade",methods=['GET','POST'])
def grade():
    if not 'user' in session:
        return redirect(url_for('home'))
    db=get_db()
    db.row_factory = make_dicts
    students=get_student_table()
    events=get_event_table()
    grades = get_grade_table()
    return render_template('grade.html',event=events,user=session['user'],grade=grades,student=students)

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
        query="select username, grade, remark, ename,request from Grades natural join Takes natural join Events where ename='%s' and cid in (select cid from Takes where username='%s')" % (event,session['user']['username'])
        if grade:
            query += " and grade=%s" % (grade)
        if student:
            query += " and username='%s'" % (student)
        grades=[]
        for i in query_db(query):
            grades.append(i)
        db.close()
        return render_template('grade.html',event=events,user=session['user'],grade=grades,student=students)
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
    return render_template('grade.html',user=session['user'],grade=grades,student=students,event=events)

@app.route("/setting")
def setting():
    if not 'user' in session:
        return redirect(url_for('home'))
    return render_template('grade.html',user=session['user'])
@app.route("/feedback")
def feedback():
    if not 'user' in session:
        return redirect(url_for('home'))
    return render_template('grade.html',user=session['user'])

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