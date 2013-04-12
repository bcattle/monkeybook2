from flask import request
from flask.ext.login import current_user
from monkeybook.models import FacebookFriend, Book, User
from monkeybook.resources.base import CurrentUserResource, ListMixin


class FriendResource(CurrentUserResource, ListMixin):
    fields = {'id', 'name', 'pic_square', 'top_friends_score'}
    depends_on_task = 'monkeybook.tasks.top_friends.top_friends_task'

    def get_depends_on_task_name(self, url=None):
        return self.depends_on_task

    def get_matching_friends(self):
        user = current_user._get_current_object()
        name_search = request.args.get('name__icontains')
        # note: it's 3x faster to perform one call vs. `FBF.objects().filter()`
        if name_search:
            return FacebookFriend.objects(user=user, name_uppercase__contains=name_search.upper())
        else:
            return FacebookFriend.objects(user=user)

    def get_queryset(self):
        return self.get_matching_friends()


# TODO: perform this with a map/reduce?
class FriendInAppResource(FriendResource):
    def get_friend_ids_in_app(self):
        # Need to return `friends` that have a User document
        friend_ids = self.get_matching_friends().scalar('uid')
        # User models having those ids
        return User.objects(id__in=friend_ids).sclar('id')

    def get_queryset(self):
        # User models having those ids
        friend_ids_in_app = self.get_friend_ids_in_app()
        # Friend models with those ids
        return FacebookFriend.objects(uid__in=friend_ids_in_app)


# TODO: perform this with a map/reduce
class FriendNotInAppResource(FriendInAppResource):
    def get_queryset(self):
        # User models having those ids
        friend_ids_in_app = self.get_friend_ids_in_app()
        # Friend models with those ids
        return FacebookFriend.objects(uid__nin=friend_ids_in_app)


class FriendBooksResource(FriendResource):
    fields = {'id', 'name', 'pic_square', 'top_friends_score'}

    def get_queryset(self):
        friend_ids = self.get_matching_friends().scalar('uid')
        # Need to return Books belonging to these friends
        return Book.objects(__raw__={ 'user.$id': {'$in': list(friend_ids)}})

        # TODO: clever ordering here -- friend order, book created
