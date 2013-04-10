
# from monkeybook.tasks.fql import *
# from monkeybook.tasks.profile import *
# from monkeybook.tasks.top_friends import *

from monkeybook.models import User, UserTask

# from celery import Celery
# celery = Celery()
# Task = celery.create_task_cls()

from monkeybook import celery

# class LoggedUserTask(Task):
class LoggedUserTask(celery.Task):
    """
    A task that logs itself to the database
    """
    abstract = True

    def apply_async(self, *args, **kwargs):
        # Enqueue the task
        async_result = super(LoggedUserTask, self).apply_async(*args, **kwargs)

        # Have to do this because Celery garbles the args
        user_id = self._get_real_kwargs(*args, **kwargs)['user_id']

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

    def _get_real_kwargs(self, *args, **kwargs):
        """
        Args can come in two places ----
          If called as  RunFqlTask().s(task_cls=ProfileFieldsTask, user_id=u.id).apply_async()              the args are in     args[1]
          If called as  RunFqlTask().apply_async(kwargs={'task_cls': GetFriendsTask, 'user_id': user_id,})  the args are in     kwargs['kwargs']
        """
        real_kwargs = kwargs['kwargs'] if 'kwargs' in kwargs else args[1]
        return real_kwargs
