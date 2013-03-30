import json
from flask import render_template, url_for, request, Response, redirect
from flask.ext.login import current_user, login_required, logout_user, login_user
from facebook import parse_signed_request
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


@app.route('/api/login', methods=['POST'])
def api_login():
    """
    This endpoint receives a POST request from client-side login
    It performs validation of the returned token, creates
    a new account if needed, and logs the user in
    """
    # request.json.keys()  -->  [u'expiresIn', u'userID', u'signedRequest', u'accessToken']
    app.logger.info('Received signed request from user %s' % request.json['userID'])
    parsed_request = parse_signed_request(request.json['signedRequest'], app.config['FB_APP_SECRET'])
    if parsed_request:
        # The request was good, is this a new user?


        # Create an account for the user, pull their profile, and save the access token
        import ipdb
        ipdb.set_trace()

        # Log the user in
        login_user(user)

        # Log here and to mixpanel
        app.logger.info('User %s successfully authenticated')
    else:
        # The request failed to validate: log an error and return http 400
        app.logger.warning('Signed request failed to validate, user %s' % request.json['userID'])
        return Response(json.dumps({
            'status': 'error',
            'message': 'Signed request failed to authenticate'
        }), status=400, mimetype='application/json')


@app.route('/logout')
@login_required
def login():
    logout_user()
    return redirect(url_for('homepage'))


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
