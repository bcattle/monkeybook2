from flask import abort
from flask.ext.restful import Resource
from monkeybook.resources.base import CurrentUserMixin
from monkeybook.books import ALL_BOOKS


class BookResource(Resource, CurrentUserMixin):
    def get_depends_on_task_name(self, url, book_type):
        # Look up the book and return the proper task
        book = ALL_BOOKS.get(book_type)
        return book.run_task_name

    def is_authorized(self, fb_id):
        return self.is_current_user(fb_id)

    def post(self, fb_id, book_type):
        """
        An empty POST to this endpoint
        spins off the `run_book` task
        """
        if not self.is_authorized(fb_id):
            abort(403)

        book = ALL_BOOKS.get(book_type)
        if book is None:
            abort(404)

        # Run the book's task
        print 'POST recieved for book %s' % book.title

        pass

