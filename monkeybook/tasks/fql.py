import datetime
from celery.utils.log import get_task_logger
from monkeybook import celery
from monkeybook.models import User, UserTask
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


@celery.task(base=RunFqlBaseTask)
def get_result_or_run_fql(task_cls, user_id, commit=True, stale_mins=15, *args, **kwargs):
    """
    Look at the UserTask collection to see
    if there is already a task with the given age

    This returns an ASYNC RESULT!
    """
    import ipdb
    ipdb.set_trace()

    task_name = '%s:%s' % (run_fql.name, task_cls().name)
    task_stale_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=stale_mins)
    user = User.objects.get(id=user_id)
    tasks = UserTask.objects(user=user, task_name=task_name, created__gt=task_stale_time)
    if tasks:
        task = tasks[0]
        # Get the task id and return the state
        task_async = celery.AsyncResult(task.task_id)
        # Note that we can create an AsyncResult with ANY ID, no exception is thrown
        # A task with a made-up id is 'PENDING'
        # so we need to check if the result exists,
        if task_async.state != 'PENDING' or task_async.state != 'FAILED':
            # Return the async result so the child can decide whether to wait
            return task_async

    # Task doesn't exist, run it
    task_async = run_fql.delay(task_cls, user_id, commit, *args, **kwargs)
    return task_async
