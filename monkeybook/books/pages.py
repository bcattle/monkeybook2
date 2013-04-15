"""
Base pages.
These are *abstract*, because they still need
    (1) an inclusion criteria - based on the book, is the page in or out?
    (2) an assignment function - grab the appropriate images from the book
        and assign them to the page
"""
from flask import render_template


class BasePage(object):
    def __init__(self, template=None, priority=0, required=False):
        """
        priority = the order in which pages get assigned
        required = the book is scrubbed if this page isn't included
        """
        self.template = template
        self.force_landscape = False
        self.priority = priority
        self.required = required

    def get_page_context(self):
        raise NotImplementedError

    def render_page(self):
        """
        Renders self.template w/ result of calling `get_page_context`
        """
        context = self.get_page_context()
        return render_template(self.template, **context)

    def is_page_included(self, book):
        """
        Looking at the book,
        is this page in or out?
        """
        raise NotImplementedError

    def assign_page(self, book):
        """
        If the page is in, grab the appropriate images
        and tag them as used
        """
        raise NotImplementedError


class StaticPage(BasePage):
    """
    Returns an empty div with a background image
    """
    template = 'full_bleed.html'

    def __init__(self, background_img, **kwargs):
        self.background_img = background_img
        super(StaticPage, self).__init__(**kwargs)

    def get_page_context(self):
        return {
            'background_img': self.background_img
        }


class PhotoPage(BasePage):
    template = 'full_bleed_editable.html'


class PhotoPageDoublePort(BasePage):
    template='lands_sq_port_dbl_port.html'


class PhotoWithCommentPage(PhotoPage):
    template = 'photo_w_comment.html'


class PhotoWithCommentPage(PhotoPage):
    template = 'photo_w_comment.html'

    def get_page_context(self):
        """
        Add the top comment, commenter's name and photo
        """
        photo = self.get_photo()
        page_content = self.get_photo_content(photo)
        top_comment = photo.get_top_comment()
        if top_comment:
            page_content['comment'] = top_comment['text']
            page_content['comment_name'] = top_comment['user_name']
            page_content['comment_pic'] = top_comment['user_pic']
        return page_content


class TopFriendNamePage(PhotoPage):
    template = 'top_friend_name.html'


class TopStatusPage(FieldPage):
    template='top_status.html'


class BirthdayPage(FieldPage):
    pass


class FriendsCollagePage(YearbookPage):
    pass


class RequiredPageFailedException(Exception):
    pass

class PageFactory(object):
    """
    Handles running the logic of
        - running the pages in order of priority
        - figuring out which pages are included
        - scrubbing the book if a required page fails
    """
    pages = None

    def __init__(self, book):
        assert self.pages

        # Get pages in order of priority
        pages_by_priority = sorted(self.pages, key=lambda x: -x.priority)

        for page in pages_by_priority:


        pass


