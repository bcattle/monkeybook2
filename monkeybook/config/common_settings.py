
## Photo

LOWEST_SQUARE_ASPECT_RATIO  = 0.9        # How low can the aspect ratio be for a photo to be considered "square"?
HIGHEST_SQUARE_ASPECT_RATIO = 1.1        # How high?


## FQL

FQL_TASK_PREFER_CACHE = False
FQL_TASK_STORE_RESULTS = True


## Celery

CELERY_DISABLE_RATE_LIMITS = True


## Security

SECRET_KEY = '\x89)_\x9d\xb2:\xd9}\xe4<G*\x00\x02\x89K\x1f\xc5\x81\xf5\xadVB\x10'

SECURITY_PASSWORD_HASH = 'pbkdf2_sha512'
SECURITY_PASSWORD_SALT = '|4l\x05pK\xba\xb4\x00\x8f\xe9\xc6\xee\xd6MHth\xa9^=n\xeb\xf2\x07\xcb\xa7\x87\xcf\xc1Y3'

CSRF_COOKIE_NAME = 'csrftoken'


## Facebook

FACEBOOK_APP_SCOPE = 'email,user_birthday,user_relationships,user_likes,user_photos,' \
                     'user_location,user_checkins,user_status,friends_likes,' \
                     'friends_photos,read_stream'


## Amazon AWS

AWS_ACCESS_KEY_ID = 'AKIAJNKCFRLQ6NGG44AQ'
AWS_SECRET_ACCESS_KEY = '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'

