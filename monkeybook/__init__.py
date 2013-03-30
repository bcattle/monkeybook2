from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.login import LoginManager
from flask.ext.seasurf import SeaSurf
from raven.contrib.flask import Sentry


app = Flask(__name__)
#app.config.from_envvar('MONKEYBOOK_SETTINGS')
app.config.from_object('monkeybook.config.dev.settings')

db = MongoEngine(app)
csrf = SeaSurf(app)

if app.config['IS_LIVE']:
    sentry = Sentry(app)

from monkeybook.models import *

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(userid):
    return Users.objects.get(userid)

from monkeybook.views import *

@app.context_processor
def template_extras():
    return {
        'MIXPANEL_API_TOKEN': app.config['MIXPANEL_API_TOKEN'],
        'DEBUG': app.config['DEBUG'],
        'IS_LIVE': app.config['IS_LIVE']
    }
