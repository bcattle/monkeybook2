import datetime
from blinker import Namespace
from flask.ext.login import current_user
from monkeybook import app
from monkeybook.fql.profile import ProfileFieldsTask, SquareProfilePicTask
from monkeybook.tasks import RunFqlTask, ExtendAccessTokenTask

namespace = Namespace()

user_created = namespace.signal('user-created')
user_logged_in = namespace.signal('user-logged-in')
user_logged_out = namespace.signal('user-logged-out')

@user_created.connect
def on_user_created(sender, user_id, provider, **extra):
    app.logger.info('User %s created' % user_id)

    # Pull the user's profile fields and larger profile pic
    RunFqlTask().apply_async(kwargs={'task_cls': ProfileFieldsTask, 'user_id': user_id,})
    RunFqlTask().apply_async(kwargs={'task_cls': SquareProfilePicTask, 'user_id': user_id,})

    # Extend their access token
    ExtendAccessTokenTask().apply_async(kwargs={'user_id': user_id,})

    # Pull their friends

    # Associate the user with that username in Mixpanel
    pass


@user_logged_in.connect
def on_user_logged_in(sender, user_id, provider, **extra):
    app.logger.info('User %s return login' % user_id)
    # Log the user's login to the db
    current_user.logins.append(datetime.datetime.utcnow())
    current_user.save()


@user_logged_out.connect
def on_user_logged_out(sender, user_id, **extra):
    app.logger.info('User %s logged out' % user_id)

