import json
from flask import url_for, request, Response, redirect, current_app
from flask.ext.login import login_required, logout_user, login_user, user_logged_in
from mongoengine.queryset import DoesNotExist
from facebook import parse_signed_request
from monkeybook import app
from monkeybook.models import Users, AccessToken
from monkeybook.signals import user_created


@app.route('/api/login/', methods=['POST'])
def api_login():
    """
    This endpoint receives a POST request from client-side login
    It performs validation of the returned token, creates
    a new account if needed, and logs the user in
    """
    import ipdb
    ipdb.set_trace()

    # request.json.keys()  -->  [u'expiresIn', u'userID', u'signedRequest', u'accessToken']
    user_id = request.json['userID']
    provider = 'facebook'
    app.logger.info('Received signed request from user %s' % user_id)
    parsed_request = parse_signed_request(request.json['signedRequest'], app.config['FB_APP_SECRET'])
    if parsed_request:
        # The request was good, is this a new user?
        try:
            user = Users.objects.get(fb_id=user_id)
            new_user = False
            # Fire the signal
            user_logged_in.send(current_app._get_current_object(), user_id=user_id, provider=provider)

        except DoesNotExist:
            # Create an account for the user and save the access token
            user = Users(fb_id=user_id)
            token = AccessToken(
                provider=provider,
                access_token=request.json['accessToken'],
                # secret=request.json['signedRequest']['code']
            )
            user.access_tokens.append(token)
            user.save()
            new_user = True
            # Fire the signal. This will pull their profile
            user_created.send(current_app._get_current_object(), user_id=user_id, provider=provider)
            # Log the user in
        login_user(user)
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
    logout_user()
    return redirect(url_for('homepage'))

