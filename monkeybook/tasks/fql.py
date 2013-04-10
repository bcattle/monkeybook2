from celery.utils.log import get_task_logger
from monkeybook import celery
from monkeybook.models import User
from monkeybook.tasks import LoggedUserTask

logger = get_task_logger(__name__)


class RunFqlBaseTask(LoggedUserTask):
    abstract = True

    # We do this so we can override the task name going into the db
    def apply_async(self, *args, **kwargs):
        async_result = super(LoggedUserTask, self).apply_async(*args, **kwargs)

        real_kwargs = self._get_real_kwargs(*args, **kwargs)
        user_id = real_kwargs['user_id']
        task_cls = real_kwargs['task_cls']

        log_name = '%s:%s' % (self.name, task_cls().name)
        self.log_task(async_result, user_id, log_name=log_name)
        return async_result


@celery.task(base=RunFqlBaseTask)
def run_fql(task_cls, user_id, commit=True, *args, **kwargs):
    """
    commit: do we call task.save()?
    """
    # Make the API Call
    task = task_cls()
    # self.name = '%s:%s' % (self.name, task.name)
    user = User.objects.get(id=user_id)
    results = task.run(user)
    if commit:
        # Store the info
        task.save(results[task.name])
    return results