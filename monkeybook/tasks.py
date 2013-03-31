from celery import Task
from monkeybook.models import Users, UserTasks


class LoggedUserTask(Task):
    """
    A task that logs the user's task to the database
    """
    def run(self, user=None, user_id=None, *args, **kwargs):
        assert user or user_id
        # Resolve the user object and store it
        self.user = user or Users.objects.get(fb_id=user_id)
        # Store the task to the db
        ut = UserTasks(user=user, task_name=self.name, task_id=self.request.id)
        ut.save()

    # def after_return(self, status, retval, task_id, args, kwargs, einfo):
    #     pass


class PullUserProfileTask(LoggedUserTask):
    def run(self, provider, user_id):
        super(PullUserProfileTask, self).run(user_id=user_id)
        pass
        # Make the API Call

        # Store the info

        # Associate the user with that username in Mixpanel

