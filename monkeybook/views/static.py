from flask import render_template
from monkeybook import app

## Static pages

@app.route('/about/')
def about_us():
    return render_template('about.html')

@app.route('/privacy/')
def privacy():
    return render_template('privacy.html')

@app.route('/terms/')
def terms():
    return render_template('terms.html')

@app.route('/contact/')
def contact():
    return render_template('contact.html')
