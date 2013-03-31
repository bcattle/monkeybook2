from flask import url_for, render_template
from flask.ext.login import current_user, login_required
from monkeybook import app


@app.route('/')
def homepage():
    # If user is logged in and has a connection to facebook
    if current_user.is_authenticated():
        template = 'dashboard.html'
        context = {}
    else:
        template = 'homepage.html'
        context = {
            'fb_app_id': app.config['FB_APP_ID'],
            'fb_scope': app.config['FACEBOOK_APP_SCOPE'],
            'login_succeeded_url': url_for('loading')
        }
    return render_template(template, **context)


@app.route('/loading/')
@login_required
def loading():
    """
    This page shows the loading screen
    The client fires off the yearbook creation process
    """
    pass
