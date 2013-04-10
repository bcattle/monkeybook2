from monkeybook import app, celery
from monkeybook.models import User, AccessToken
from monkeybook.tasks import celery, LoggedUserTask
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@celery.task(base=LoggedUserTask)
def extend_access_token_task(user_id):
    user = User.objects.get(id=user_id)
    graph = user.get_fb_api()
    result = graph.extend_access_token(app.config['FB_APP_ID'], app.config['FB_APP_SECRET'])

    logger.info('Extended access token for user %s, expires in %s seconds'
                % (user.username or user.id, result['expires']))

    # Save the access token
    token = AccessToken(
        provider='facebook',
        access_token=result['access_token'],
        )
    user.access_tokens.append(token)
    user.save()
    return result

