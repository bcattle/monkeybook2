import urllib
from flask import abort, request
from flask.ext.login import current_user
from flask.ext.restful import Resource as RestfulResource
from werkzeug.datastructures import MultiDict
from monkeybook import api
from monkeybook.models import FacebookFriend, Book


PER_PAGE = 20

class SimplePaginator(object):
    def __init__(self, queryset):
        self.queryset = queryset
        self.length = len(queryset)

    def get_page(self, offset, limit=PER_PAGE):
        """
        Returns a page of results from the queryset
        """
        return self.queryset[offset:offset+limit]

    def get_next_url(self, offset, limit=PER_PAGE):
        """
        Generates a next url relative to the current request
        Limit needs to be correct to keep within range
        If we are at the end, return nothing
        """
        qs_len = len(self.queryset)
        new_offset = offset + limit
        if new_offset >= qs_len:
            return None
        remaining = qs_len - offset
        new_limit = remaining if remaining < limit else limit

        new_args = MultiDict(request.args.items())
        new_args['offset'] = new_offset
        new_args['limit'] = new_limit
        return '%s?%s' % (request.base_url, urllib.urlencode(new_args))

    def parse_pagination_args(self):
        """
        Pulls out `limit` and `offset` from GET string
        """
        DEFAULT_OFFSET = 0
        DEFAULT_LIMIT = PER_PAGE
        offset, limit = request.args.get('offset', DEFAULT_OFFSET), request.args.get('limit', DEFAULT_LIMIT)
        # Coerce to int
        try:
            offset = int(offset)
        except ValueError:
            offset = DEFAULT_OFFSET
        try:
            limit = int(limit)
        except ValueError:
            limit = DEFAULT_LIMIT
        return offset, limit


class CurrentUserMixin(object):
    def is_current_user(self, fb_id):
        return current_user.is_authenticated() and str(fb_id) == current_user.id


class CurrentUserResource(RestfulResource, CurrentUserMixin):
    def is_authorized(self, fb_id):
        return self.is_current_user(fb_id)

    def get(self, fb_id):
        if not self.is_authorized(fb_id):
            abort(403)

        queryset = self.get_queryset()
        # queryset = self.filter_queryset(queryset)

        total = len(queryset)
        paginator = SimplePaginator(queryset)
        offset, limit = paginator.parse_pagination_args()
        # Have to do this here because oddly, indexing the queryset throws away the other items
        next_url = paginator.get_next_url(offset, limit)
        page = paginator.get_page(offset, limit)

        results = {
            'meta': {
                'offset': offset,
                'limit': limit,
                'total': total,
                },
            'objects': self._make_response_data(page)
        }

        if next_url:
            results['meta']['next'] = next_url
        return results

    # def filter_queryset(self, queryset):
    #     return queryset


class ListMixin(CurrentUserResource):
    def _make_response_data(self, data):
        # Generate a list with the desired fields
        response_data = []
        for item in data:
            if hasattr(self, 'fields'):
                item_data = {}
                for name, val in item._data.items():
                    if name in self.fields:
                        item_data[name] = val
                response_data.append(item_data)
            else:
                response_data.append(item._data)
        return response_data


class FriendResource(CurrentUserResource, ListMixin):
    fields = {'id', 'name', 'pic_square', 'top_friends_score'}

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


# TODO: perform this with a map/reduce
class FriendInAppResource(FriendResource):
    def get_queryset(self):
        friends = self.get_matching_friends()
        # Need to return `friends` that have a User document
        pass


# TODO: perform this with a map/reduce
class FriendNotInAppResource(FriendResource):
    def get_queryset(self):
        friends = self.get_matching_friends()
        # Need to return `friends` that DO NOT have a User document
        pass


class FriendBooksResource(FriendResource):
    fields = {'id', 'name', 'pic_square', 'top_friends_score'}

    def get_queryset(self):
        friend_ids = self.get_matching_friends().scalar('uid')
        # Need to return Books belonging to these friends
        return Book.objects(user_id__in=friend_ids)         # <-- this is wrong, figure out how to filter by user.id

        # TODO: clever ordering here -- friend order, book created



api.add_resource(FriendResource,         '/friends')
api.add_resource(FriendInAppResource,    '/friends/in-app')
api.add_resource(FriendNotInAppResource, '/friends/not-in-app')
api.add_resource(FriendBooksResource,    '/friends/books')
