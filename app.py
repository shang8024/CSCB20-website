# required imports
import sqlite3
from flask import Flask, render_template, request, g

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
    db=get_db()
    db.row_factory = make_dicts
    employees=[]
    for employee in query_db('select * from employees'):
        employees.append(employee)
    db.close()
    return render_template('index.html',employee=employees)

@app.route('/login')
def add_todo():
    return 

@app.route('/signup')
def clear_todo():
    global todo_list
    todo_list = []
    return root()

if __name__ == '__main__':
    # we set debug=True so you don't have to restart the app everything you make changes
    # just refresh the browser after each change
    app.run(debug=True)