from blinker import Namespace
from monkeybook import app
from monkeybook.tasks import PullUserProfileTask

namespace = Namespace()

user_created = namespace.signal('user-created')
user_logged_in = namespace.signal('user-logged-in')
user_logged_out = namespace.signal('user-logged-out')

@user_created.connect
def on_user_created(sender, user_id, provider, **extra):
    # Pull the user's profile from facebook
    # PullUserProfileTask.delay(provider=provider, user_id=user_id)
    pass

@user_logged_in.connect
def on_user_logged_in(sender, user_id, provider, **extra):
    # Log here and to mixpanel
    app.logger.info('User %s successfully authenticated' % user_id)

@user_logged_out.connect
def on_user_logged_out(sender, **extra):
    pass
