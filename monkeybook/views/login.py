import json
from flask import url_for, request, Response, redirect, current_app
from flask.ext.login import login_required, logout_user, login_user, user_logged_in, current_user
from mongoengine.queryset import DoesNotExist
from facebook import parse_signed_request
from monkeybook import app
from monkeybook.models import User, AccessToken
from monkeybook.signals import user_created, user_logged_out


@app.route('/api/login/', methods=['POST'])
def api_login():
    """
    This endpoint receives a POST request from client-side login
    It performs validation of the returned token, creates
    a new account if needed, and logs the user in
    """
    # request.json.keys()  -->  [u'expiresIn', u'userID', u'signedRequest', u'accessToken']
    user_id = request.json['userID']
    provider = 'facebook'
    app.logger.debug('Received signed request from user %s' % user_id)
    parsed_request = parse_signed_request(request.json['signedRequest'], app.config['FB_APP_SECRET'])
    if parsed_request:
        # The request was good, is this a new user?
        try:
            user = User.objects.get(id=user_id)
            new_user = False
            signal = user_logged_in

        except DoesNotExist:
            # Create an account for the user
            user = User(id=user_id)
            new_user = True
            signal = user_created

        # Save the access token
        token = AccessToken(
            provider=provider,
            access_token=request.json['accessToken'],
        )
        user.access_tokens.append(token)
        user.save()

        # Log the user in
        login_user(user)

        # Run the signal handler. If new user, this will pull their profile
        signal.send(current_app._get_current_object(), user_id=user_id, provider=provider)

        # Return success
        return Response(json.dumps({'new_user': new_user}), status=201, mimetype='application/json')
    else:
        # The request failed to validate: log an error and return http 400
        app.logger.warning('Signed request failed to validate, user %s' % user_id)
        return Response(json.dumps({
            'status': 'error',
            'message': 'Signed request failed to authenticate'
        }), status=400, mimetype='application/json')


@app.route('/logout/')
@login_required
def logout():
    user_id = current_user.id
    logout_user()
    # Fire the signal
    user_logged_out.send(current_app._get_current_object(), user_id=user_id)
    # Redirect
    return redirect(url_for('homepage'))

