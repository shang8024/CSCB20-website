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
  - Students can now request a remark by filling in the remark section next to their grades on "grade" page. Each person can only submit a remark request to his/her instructor for each assignment/test. Once an instructor responsed to the request, the student will see the mark and the remark status changed.
## 3-27
  - Instructor now can check remark request. I wrote a javascript to swicth remark status between remarking grades and all grades. The javascript may be developed to deal with username sort, grade sort and type sort later. Instructors can now enter students grade by inbox above student gradetable. The input must not be empty and an instructor can only enter the grade of students belongs to him. 
## 3-28
  - 老师可以添加、更改成绩了。
