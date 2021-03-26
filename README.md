# CSCB20
a website for cscb63
## 3-24
  - 把Chris Qiu写入footer的website designer名单
  - Completed database shcema and inserted some dummy data
## 3-25 
  - Wrote some basic login function. The current user's information (username, first name, last name, type) is stored in a json type session['user'].
  - The user can see the welcome message like "Welcome, Student/Instructor XXX" after logging in the "home.html".
  - Preliminarily established the framework of the grade page of student module, and I will continue working on "remark" function tomorrow.
## 3-26
  - 发现了Abbas没有告诉我们在写入database之后要用“db.commit()”才会保存的问题。
  - Students can now request a remark by filling in the remark section next to their grades on "grade" page. Each person can only submit a remark request to his/her instructor for each assignment/test.
