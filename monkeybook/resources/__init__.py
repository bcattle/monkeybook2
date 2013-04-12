from monkeybook import api
from monkeybook.resources.friends import *
from monkeybook.resources.progress import *
from monkeybook.resources.book import *


# Friends
api.add_resource(FriendResource,         '/friends')
api.add_resource(FriendInAppResource,    '/friends/in-app')
api.add_resource(FriendNotInAppResource, '/friends/not-in-app')
# Friends - progress
api.add_resource(ProgressResource,       '/friends/progress')
api.add_resource(ProgressResource,       '/friends/in-app/progress')
api.add_resource(ProgressResource,       '/friends/not-in-app/progress')
# Friends books
api.add_resource(FriendBooksResource,    '/friends/books')

# Books
# api.add_resource(BookResource,          '/books/<book_type>', '/books/<book_type>/<id>')
api.add_resource(BookResource,          '/books/<book_type>')
api.add_resource(ProgressResource,  '/books/<book_type>/progress', endpoint='bookprogressresource')
