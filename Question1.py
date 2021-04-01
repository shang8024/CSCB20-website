# required imports; you may add more in the future
from flask import Flask, render_template, request

# tells Flask that "this" is the current running app
app = Flask(__name__)

# setup the default route
# this is the page the site will load by default (i.e. like the home page)
@app.route('/<s>')
def generateResponse(s):
    if (s.isalpha() and s.isupper()):
        name = s.lower()
    elif (s.isalpha() and s.islower()):
        name = s.upper()
    else:
        name = ''.join(i for i in s if not i.isnumeric())
    return "Welcome, %s, to my CSCB20 website!" % (name)

if __name__ == '__main__':
    app.run(debug=True)