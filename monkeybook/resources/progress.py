from flask import abort, request
from flask.ext.login import current_user
from flask.ext.restful import Resource as RestfulResource
from werkzeug.exceptions import MethodNotAllowed
from monkeybook import app, celery
from monkeybook.models import UserTask
from monkeybook.resources.base import CurrentUserMixin


# TASK_STALE_MINS = 10

class ProgressResource(RestfulResource, CurrentUserMixin):
    """
    This resource allows us to query the progress of the tasks
    that other resources depend on.

    For example, FriendResource has an attr ----
        depends_on_task = 'monkeybook.tasks.top_friends.top_friends_task'

    Register this resource by calling
        api.add_resource(ProgressResource,       '/friends/progress')

    When a request comes in, the URL is resolved back to '/friends'
        --> FriendResource. This class checks the db collection UserTask
        for an instance of 'monkeybook.tasks.top_friends.top_friends_task',
        and returns its status.
    """

    def is_authorized(self, fb_id):
        return self.is_current_user(fb_id)

    def get(self, fb_id, **kwargs):
        if not self.is_authorized(fb_id):
            abort(403)

        user = current_user._get_current_object()

        # We use the url to decide which Resource the user is targeting
        resource_url = request.path.rsplit('/progress', 1)[0]
        adapter = app.create_url_adapter(request)

        # match() only matches if the *request method* is correct
        # GET by default
        try:
            endpoint = adapter.match(resource_url)[0]
        except MethodNotAllowed:
            # Try POST
            try:
                endpoint = adapter.match(resource_url, method='POST')[0]
            except MethodNotAllowed:
                # Not GET or POST
                raise Exception('Unable to resolve url <%s> to endpoint. '
                                'Either URL is wrong or it doesn\'t support GET or POST')

        resource_class = app.view_functions[endpoint].view_class
        resource_instance = resource_class()

        # Some resources call different tasks based on URL
        task_name = resource_instance.get_depends_on_task_name(resource_url, **kwargs)
        if task_name is None:
            raise AttributeError('Can\'t get progress of a task without the attr `depends_on_task`')

        # Check the UserTask to get the latest task with that name

        # Cases:
        #  - No matching UserTask
        #  - UserTask matches
        #  - UserTask matches but its old

        #        task_stale_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=TASK_STALE_MINS)
        tasks = UserTask.objects(user=user, task_name=task_name)
        if tasks:
            task = tasks[0]
            # Get the task id and return the state
            task_async = celery.AsyncResult(task.task_id)

            return {
                'task_id': task.task_id,
                'created': str(task.created),
                'state': task_async.state
            }
        else:
            # No tasks in DB, return a different status
            app.logger.debug('User %s, looking for task %s, none found in db' % (user, task_name))

            return {
                'task_id': '',
                'created': '',
                'state': 'NOT_STARTED'
            }
