from flask import render_template
from monkeybook import app, social

@app.route('/')
def homepage():
    # if user_is_logged_in:
    #     template = 'dashboard.html'
    # else:
    template = 'homepage.html'
    return render_template(template, fb_conn=social.facebook.get_connection())

#@login_required

