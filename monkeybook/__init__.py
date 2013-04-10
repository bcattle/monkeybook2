from flask import Flask, redirect
from flask.ext.mongoengine import MongoEngine
from flask.ext.login import LoginManager, logout_user
from flask.ext.seasurf import SeaSurf
from flask.ext.restful import Api
from raven.contrib.flask import Sentry
from celery import Celery


app = Flask(__name__)

#app.config.from_envvar('MONKEYBOOK_SETTINGS')
MONKEYBOOK_SETTINGS = 'monkeybook.config.dev.settings'
app.config.from_object(MONKEYBOOK_SETTINGS)

db = MongoEngine(app)
csrf = SeaSurf(app)

if app.config['IS_LIVE']:
    sentry = Sentry(app)

from monkeybook.models import *


## Login

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
    try:
        return User.objects.get(userid)
    except DoesNotExist:
        # User got deleted, log them out
        logout_user()

@login_manager.unauthorized_handler
def redirect_home():
    return redirect(url_for('homepage'))

## Celery

celery = Celery('monkeybook')
# celery.config_from_envvar('MONKEYBOOK_SETTINGS')
celery.config_from_object(MONKEYBOOK_SETTINGS)


## Views

from monkeybook.views import *

@app.context_processor
def template_extras():
    return {
        'MIXPANEL_API_TOKEN': app.config['MIXPANEL_API_TOKEN'],
        'DEBUG': app.config['DEBUG'],
        'IS_LIVE': app.config['IS_LIVE']
    }
