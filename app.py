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
    username=session['user']['username']
    if session['user']['type']:
        # getting all the students' grades of the instroctor's classes
        for grade in query_db("select distinct username, grade, remark, ename,request from Grades natural join Takes where cid in (select cid from Takes where username=?)", [username]):
            grades.append(grade)
    else:
        # getting all the grades of the student
        for grade in query_db("select * from Grades where username=?", [username]):
            grades.append(grade)
    db.close()
    return grades

def get_student_table():
    # return usernames of students who are in the same class with the current user(instructor).
    db=get_db()
    db.row_factory = make_dicts
    students=[]
    username=session['user']['username']
    for i in query_db("select distinct username from Takes natural join Users where type=0 and cid in (select cid from Takes where username=?)", [username]):
        students.append(i)
    return students

def get_event_table():
    # get all enames from Grades table
    db=get_db()
    db.row_factory = make_dicts
    events=[]
    for j in query_db('select distinct ename from Grades'):
        events.append(j)
    return events

def grade_changes(student,event,grade):
    user=session['user']['username']
    db=get_db()
    db.row_factory = make_dicts
    grades=query_db("select * from Grades where username=? and ename=?",[student,event],one=True)
    if not grades:
        # grade(student,event) does not exist
        # insert value(student,event,grade,0) into Grades(username,ename,grade,remark)
        query_db("insert into Grades(username,ename,grade,remark) values(?,?,?,0)", [student,event,grade]) 
    else:
        # grade(student,event) exist, update existing row.
        if grades['remark'] == 1:
            # if the student is requesting a remark for that grade, set the remark status to 'remarked'
            grades['remark'] = -1
        remark=grades['remark']
        query_db("update Grades set remark=?, grade=? where ename=? and username=?", [remark,grade,event,student])
    # commit change
    db.commit()

# tells Flask that "this" is the current running app
app = Flask(__name__)
app.secret_key = os.urandom(12)

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
        # if logged in, render index.html
        # if not, back to login.html
        return render_template('index.html',user=session['user'])

@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method=='POST':
        if 'signup' in request.form:
            return redirect(url_for('signup'))
        # when user submited, receive input values
        login_name = request.form['username']
        db=get_db()
        db.row_factory = make_dicts
        # search for Users row with the input username
        user = query_db('select * from Users where username=?',[login_name],one=True)
        if user == None:
            # error if username not in Users table
            error = 'Invalid username'
        elif request.form['password'] == user['password']:
            # if password matches the username, save user info to session and render index.html
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
            # error if password incorrect
            error = 'Invalid password'
    elif 'user' in session:
        # if logged in, render index.html
        return redirect(url_for('home'))
    # return login.html with error messages
    return render_template('login.html',error=error)

@app.route('/logout')
def logout():
    # clean user infos saved in session, return to login.html
    session.pop('user',None)
    return redirect(url_for('home'))

@app.route('/signup',methods=['GET', 'POST'])
def signup():
    db = get_db()
    db.row_factory = make_dicts
    error = None
    classes=[]
    # get class list from db
    for item in query_db('select * from Classes'):
        classes.append(item)
    if request.method == 'POST':
        # if user submit, receive inputs
        # (don't need to check whether inputs exists, java has alredy done that for us)
        curr_username = request.form['username']
        curr_f_name = request.form['first_name']
        curr_l_name = request.form['last_name']
        curr_email = request.form['email']
        curr_type = request.form['type']
        curr_ps = request.form['password']
        curr_class = request.form.getlist('check')
        if not query_db('select username from Users where username=?', [curr_username], one=True): #and #sql_uid == None):
            # if username not exist in Users (new user), update user with name, username,password,type
            query_db('INSERT INTO Users (username,first_name,last_name,password,type) VALUES (?,?,?,?,?)',[curr_username, curr_f_name, curr_l_name, curr_ps, curr_type])
            # update Takes(username,cid)
            for item in curr_class:
                query_db('INSERT INTO Takes(username,cid) values(?,?)',[curr_username,item])
            error = "Registed successfully!"
            if curr_email:
                # if email valid, update email
                query_db('update Users set email=? where username=?',[curr_email,curr_username])
            db.commit()
        else:
            # if username exists, return with error
            error = 'Username exists!!!!! Try again!'
    db.close()
    return render_template('signup.html',class_list=classes,error=error)

@app.route("/grade",methods=['GET','POST'])
def grade():
    if not 'user' in session:
    # if not logged in, back to login
        return redirect(url_for('home'))
    db=get_db()
    db.row_factory = make_dicts
    if session['user']['type']:
        # if current user is instructor, send user info, students grades of his/her, all enames in db, all hi/her students' usernames to grade_i.html
        students=get_student_table()
        events=get_event_table()
        grades = get_grade_table()
        return render_template('grade_i.html',event=events,user=session['user'],grade=grades,student=students)
    else:
        # if current user is student, send user info, his/her grades to grade_s.html 
        grades = get_grade_table()
        return render_template('grade_s.html',user=session['user'],grade=grades)

@app.route("/search-grade",methods=['GET','POST'])
def search_grade():
    if not 'user' in session:
        # if not logged in, back to login
        return redirect(url_for('home'))
    elif not session['user']['type']:
        return redirect(url_for('grade'))
    if request.method == 'GET':
        # if user searched for something
        if 'refresh' in request.args:
            return redirect(url_for('grade'))
        db=get_db()
        db.row_factory = make_dicts
        students=get_student_table()
        events=get_event_table()
        student=request.args.get('search-student')
        event=request.args.get('search-event')
        grade=request.args.get('search-grade')
        username=session['user']['username']
        grades=[]
        # for all student's grade of the user's classes, only append grades that match the filters(inputs) to the grades list
        for i in query_db("select distinct username, grade, remark, ename,request from Grades natural join Takes where cid in (select cid from Takes where username=?)",[username]):
            if (not (grade and int(grade) != i['grade'])) and (student in i['username']) and (not (event and event != i['ename'])):
                grades.append(i)
        db.close()
        # also, send user info, enames,grades,students'usernames of user's classes to grade_i.html
        return render_template('grade_i.html',event=events,user=session['user'],grade=grades,student=students)
    else:
        # if not, normal grade page
        return redirect(url_for('grade'))

@app.route("/grade-remark",methods=['GET','POST'])
def request_remark():
    if not 'user' in session:
        # if not logged in, back to login
        return redirect(url_for('home'))
    elif session['user']['type']:
        return redirect(url_for('grade'))
    else:
        db=get_db()
        db.row_factory = make_dicts
        remark_req = request.form['remark_request']
        remark_eve = request.form['remark_event']
        user=session['user']['username']
        # if student request a remark, set remark status as 1 and update request
        query_db("update Grades set remark=?, request=? where username=? and ename=?",[1,remark_req,user,remark_eve])
        db.commit()
        db.close()
    return redirect(url_for('grade'))

@app.route("/grading",methods=['GET','POST'])
def grading():
    if not 'user' in session:
        # if not logged in, back to login
        return redirect(url_for('home'))
    elif not session['user']['type']:
        return redirect(url_for('grade'))
    if request.method == 'POST':
        # if instructor submit temp changes
        # update evey grade change in list received from java
        db=get_db()
        db.row_factory = make_dicts
        # get a list of grades from java
        changes = request.json['changes']
        # for each grade in the list, apply change to Grade db
        for item in changes:
            grade_changes(item['username'],item['ename'],item['grade'])
        db.commit()
        db.close()
    #No, it won't actually rerender the page, since it is called by java, return is just for safety thought
    return redirect(url_for('grade'))

@app.route("/deleting",methods=['GET','POST'])
def deleting():
    if not 'user' in session:
        # if not logged in, back to login
        return redirect(url_for('home'))
    elif not session['user']['type']:
        return redirect(url_for('grade'))
    if request.method == 'POST':
        db=get_db()
        db.row_factory = make_dicts
        username=request.json['username']
        ename=request.json['ename']
        # delete Grades row with username,ename received from java 
        query_db('delete from Grades where username=? and ename=?',[username,ename])
        db.commit()
        db.close()
    #No, it won't actually rerender the page, since it is called by java, return is just for safety thought
    return redirect(url_for('grade'))

@app.route("/remark-sort")
def remark_sort():
    if not 'user' in session:
        # if not logged in, back to login
        return redirect(url_for('home'))
    elif not session['user']['type']:
        return redirect(url_for('grade'))
    db=get_db()
    db.row_factory = make_dicts
    grades=[]
    username=session['user']['username']
    # get all grades that remark status==1 from Grades table
    for grade in query_db("select distinct username, grade, remark, ename,request from Grades natural join Takes where remark=1 and cid in (select cid from Takes where username=?)", [username]):
        grades.append(grade)
    students=get_student_table()
    events=get_event_table()
    db.close()
    # rerender the grade_i.html with grades with remark status == 1
    return render_template('grade_i.html',user=session['user'],grade=grades,student=students,event=events)

@app.route('/feedback',methods=['GET', 'POST'])
def feedback():
    if not 'user' in session:
    # if not logged in, back to login
        return redirect(url_for('home'))
    db = get_db()
    db.row_factory = make_dicts
    name = session['user']['username']
    if session['user']['type']:
    #if the user is logged in as a instructor, get to the feedback page for instructor.
        feedbacks=[]
        for item in query_db('select qname,ans from Feedback natural join Questions where username=?',[name]):
            feedbacks.append(item)
        db.close
        return render_template('feedback_i.html',user=session['user'],feedback = feedbacks)
    else:
    #if the user is logged in as a student, get to the feedback page for student.
        instructors = []
        questions = []
        submit = ''
        for instructor in query_db('SELECT* FROM Users WHERE type == 1'):
            instructors.append(instructor)
        for question in query_db('SELECT* FROM Questions'):
            questions.append(question)
        if request.method=='POST':
            submit = 'Please do not submit everything empty!'
            for question in questions:
            #for each question, check if the student has answered it.
                answer = request.form[str(question['qid'])]
                if answer != '':
                    #if the student has filled something in the textarea, upload it into the database.
                    insert_data = [request.form['iuser'],question['qid'],answer]
                    db.execute('INSERT INTO Feedback (username,qid,ans) VALUES (?,?,?)',(*insert_data,))
                    submit = 'Submitted Successfully!'
        db.commit()
        db.close
        return render_template('feedback_s.html',user = session['user'],instructor = instructors,submit = submit,questions = questions)
    
@app.route('/setting',methods=['GET', 'POST'])
def setting():
    if not 'user' in session:
    # if not logged in, back to login
        return redirect(url_for('home'))
    error = ['','','','']
    db = get_db()
    db.row_factory = make_dicts
    username=session['user']['username']
    LEC = query_db('SELECT cname FROM Takes natural join Classes WHERE username == ?',[username])
    if request.method == 'POST':
        #check whether the key in included in the request.form to make sure which form is submitted.
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
            #if the student submit 'None' or nothing in the email form, then delete email in the database
                session['user']['email'] = 'None'
                db.execute('UPDATE Users SET email = NULL WHERE username = ?',(*[username],))
                error[3] = 'Email Deleted Successfully!'
            else:
                session['user']['email'] = request.form['email']
                db.execute('UPDATE Users SET email = ? WHERE username = ?',(*[request.form['email'], username],))
                error[3] = 'Reset Successfully!'
    db.commit()
    db.close
    return render_template('setting.html',user=session['user'],error = error,LEC=LEC)

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
    app.run(debug=True,host='0.0.0.0')
