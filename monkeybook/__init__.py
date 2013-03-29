from flask import Flask
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore
from flask.ext.social import Social
from flask.ext.social.datastore import MongoEngineConnectionDatastore


app = Flask(__name__)
#app.config.from_envvar('MONKEYBOOK_SETTINGS')
app.config.from_object('monkeybook.config.dev.settings')

db = MongoEngine(app)

from monkeybook.models import *

security = Security(app, MongoEngineUserDatastore(db, User, Role))
social = Social(app, MongoEngineConnectionDatastore(db, Connection))

from monkeybook.views import *
