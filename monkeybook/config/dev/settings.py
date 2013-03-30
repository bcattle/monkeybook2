from monkeybook.config.common_settings import *

DEBUG = True
IS_LIVE = False

## Facebook

# SOCIAL_FACEBOOK['consumer_key'] = '111183162379123',
# SOCIAL_FACEBOOK['consumer_secret'] = 'd9afe8c407fd0577883312f8b8b23204'
FB_APP_ID = '111183162379123'
FB_APP_SECRET = 'd9afe8c407fd0577883312f8b8b23204'

## Mixpanel

MIXPANEL_API_TOKEN = 'd777afd9cbbb0a60d303f18ccd05ce67'

## Database

MONGODB_DB = 'monkeybook'
MONGODB_HOST = 'localhost'
MONGODB_PORT = 27017
MONGODB_USER = 'admin'
MONGODB_PASSWORD = 'asdf'

# mongodb://[username:password@]host1[:port1][,host2[:port2]][/[database][?options]]
MONGO_URI = 'mongodb://%(user)s:%(pass)s@%(host)s:%(port)d/%(db)s' % {
    'user': MONGODB_USER,
    'pass': MONGODB_PASSWORD,
    'host': MONGODB_HOST,
    'port': MONGODB_PORT,
    'db': MONGODB_DB,
}

## Celery

BROKER_URL = MONGO_URI
CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = {
    "host": MONGODB_HOST,
    "port": MONGODB_PORT,
    "user": MONGODB_USER,
    "password": MONGODB_PASSWORD,
    "database": MONGODB_DB,
    "taskmeta_collection": "celery_taskmeta",
}

