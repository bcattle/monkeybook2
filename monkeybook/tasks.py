from celery.utils.log import get_task_logger
from monkeybook import celery, app
from monkeybook.models import User, UserTask, AccessToken

logger = get_task_logger(__name__)


class LoggedUserTask(celery.Task):
    """
    A task that logs itself to the database
    """
    def apply_async(self, *args, **kwargs):
        # Enqueue the task
        async_result = super(LoggedUserTask, self).apply_async(*args, **kwargs)

        # Weird convention, due to the fact that `kwargs` are
        # destined for the run() method, not this one
        user_id = kwargs['kwargs']['user_id']

        # Store the task to the db
        self.log_task(async_result, user_id)
        return async_result

    def log_task(self, async_result, user_id, log_name=None):
        user = User.objects.get(id=user_id)
        log_name = log_name or self.name
        ut = UserTask(user=user, task_name=log_name, task_id=async_result.id)
        ut.save()

    # def after_return(self, status, retval, task_id, args, kwargs, einfo):
    #     pass


class RunFqlTask(LoggedUserTask):
    def run(self, task_cls, user_id, commit=True, *args, **kwargs):
        """
        commit: do we call task.save()?
        """
        # Make the API Call
        task = task_cls()
        self.name = '%s:%s' % (self.name, task.name)
        user = User.objects.get(id=user_id)
        results = task.run(user)
        if commit:
            # Store the info
            task.save(results[task.name])
        return results

    # We do this so we can override the task name going into the db
    def apply_async(self, *args, **kwargs):
        async_result = super(LoggedUserTask, self).apply_async(*args, **kwargs)
        user_id = kwargs['kwargs']['user_id']
        task_cls = kwargs['kwargs']['task_cls']
        log_name = '%s:%s' % (self.name, task_cls().name)
        self.log_task(async_result, user_id, log_name=log_name)
        return async_result


class ExtendAccessTokenTask(LoggedUserTask):
    def run(self, user_id):
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

