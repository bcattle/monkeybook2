import datetime
from decimal import Decimal
from pytz import utc
from flask.ext.login import UserMixin
from mongoengine import *
from monkeybook import app
from facebook import GraphAPI
from monkeybook.utils import short_url
# Really, should subclass models that depend on this and stick in a yearbook2012.models
from monkeybook.books.yearbook2012.settings import *

FB_ID_FIELD_LENGTH = 30
LOWEST_SQUARE_ASPECT_RATIO = app.config['LOWEST_SQUARE_ASPECT_RATIO']
HIGHEST_SQUARE_ASPECT_RATIO = app.config['HIGHEST_SQUARE_ASPECT_RATIO']


class AccessToken(EmbeddedDocument):
    provider = StringField(max_length=255, required=True)
    access_token = StringField(max_length=255, required=True)
    created = DateTimeField(default=lambda: datetime.datetime.utcnow())


class FamilyMember(EmbeddedDocument):
    id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    relationship = StringField(max_length=10)


class User(Document, UserMixin):
    id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    email = EmailField(max_length=255)
    username = StringField(max_length=255)
    active = BooleanField(default=True)
    access_tokens = SortedListField(EmbeddedDocumentField(AccessToken), ordering='created')
    locale = StringField(max_length=10)

    name = StringField(max_length=255)
    first_name = StringField(max_length=50)
    sex = StringField(max_length=50)
    birthday = DateTimeField()
    affiliations = ListField(DictField())
    age_range = DictField()
    location = DictField()
    pic_square = StringField(max_length=255)
    pic_square_large = StringField(max_length=255)

    relationship_status = StringField(max_length=10)
    significant_other_id = StringField(max_length=FB_ID_FIELD_LENGTH)
    # friends = ListField(EmbeddedDocumentField(FacebookFriend))
    family = ListField(EmbeddedDocumentField(FamilyMember))

    stripe_customer_id = StringField(max_length=255)
    logins = ListField(DateTimeField)

    def __unicode__(self):
        return self.name or ''

    @property
    def friends(self):
        return FacebookFriend.objects(user=self)

    meta = {
        'indexes': ['id']
    }

    def get_fb_api(self):
        # Access_tokens is a SortedListField, so we just index it
        latest_access_token = self.access_tokens[-1].access_token
        return GraphAPI(latest_access_token)

    def get_id_str(self):
        return self.username or self.id


class UserTask(Document):
    user = ReferenceField(User, required=True)
    task_name = StringField(max_length=255, required=True)
    task_id = StringField(max_length=255, required=True)
    created = DateTimeField(default=lambda: datetime.datetime.utcnow())

    meta = {
        'indexes': ['user', 'task_name'],
        'ordering': ['-created'],
    }


class CartItem(EmbeddedDocument):
    item = StringField(max_length=30, required=True)
    price = DecimalField(required=True)


class Address(EmbeddedDocument):
    name = StringField(max_length=255, required=True)
    address = StringField(max_length=255, required=True)
    address2 = StringField(max_length=255, required=True)
    country = StringField(max_length=255, required=True)
    city = StringField(max_length=255, required=True)
    state_province = StringField(max_length=50, required=True)
    postal = StringField(max_length=20, required=True)


class Order(Document):
    user = ReferenceField(User, required=True)
    stripe_single_use_token = StringField(max_length=255, required=True)
    items = ListField(EmbeddedDocumentField(CartItem))
    tax = DecimalField(default=Decimal(0))
    charged_total = DecimalField(default=Decimal(0))
    shipping_address = EmbeddedDocumentField(Address)


class FacebookFriend(Document):
    # Associated with *either* a user or a book
    user = ReferenceField(User)
    book = ReferenceField('Book')

    uid = StringField(max_length=FB_ID_FIELD_LENGTH, required=True)     # NOT the primary key
    name = StringField(max_length=255, required=True)
    name_uppercase = StringField(max_length=255, required=True)
    first_name = StringField(max_length=50)
    sex = StringField(max_length=10)
    pic_square = StringField(max_length=255)

    tagged_in_photos = ListField(StringField)

    top_friends_score = FloatField(default=0)
    comments_score = FloatField(default=0)
    posts_score = FloatField(default=0)
    photos_score = FloatField(default=0)
    tags = ListField(StringField)               # 'top_friend', 'top_20_friend', etc.

    meta = {
        'indexes': [('user', 'name_uppercase'), ('book', 'name_uppercase'), ('user', 'uid'), ('book', 'uid')],
        'ordering': ['user', '-top_friends_score']
    }

    def __unicode__(self):
        return self.name


class PhotoSize(EmbeddedDocument):
    height = IntField(required=True)
    width = IntField(required=True)
    url = URLField(required=True)


class ObjectComment(EmbeddedDocument):
    made_by = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    text = StringField(max_length=255, required=True)
    score = IntField(default=0)
    likes = IntField(default=0)
    user_likes = BooleanField(default=False)

    meta = {
        'ordering': ['-score']
    }


# TODO: Make the photo model abstract
# Each book inherits and creates its own, they go in the same collection

class Photo(Document):
    id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    user = ReferenceField(User, required=True)
    book = ReferenceField('Book')

    created = DateTimeField()
    height = IntField(required=True)
    width = IntField(required=True)
    url = URLField(required=True)
    all_sizes = ListField(EmbeddedDocumentField(PhotoSize))
    caption = StringField(max_length=255, required=True)
    comments = ListField(EmbeddedDocumentField(ObjectComment))
    comments_from_friends = IntField(default=0)
    like_count = IntField(default=0)

    people_in_photo = ListField(StringField)
    num_top_friends_in_photo = IntField(default=0)
    num_top_20_friends_in_photo = IntField(default=0)
    tags = ListField(StringField)
    score = FloatField(default=0)         # Or add a series of ad-hoc score fields as needed per book?

    meta = {
        'indexes': ['id'],
        'ordering': ['-score']
    }

    @property
    def num_people_in_photo(self):
        return len(self.people_in_photo) + 1        # Tagged people plus owner

    @property
    def top_friends_points(self):
        return self.num_top_friends_in_photo + self.num_top_20_friends_in_photo     # This double-counts top-20 friends, we want this

    @property
    def aspect_ratio(self):
        return float(self.width) / float(self.height)

    def is_square(self):
        return LOWEST_SQUARE_ASPECT_RATIO < self.aspect_ratio < HIGHEST_SQUARE_ASPECT_RATIO

    def is_portrait(self):
        return self.aspect_ratio < LOWEST_SQUARE_ASPECT_RATIO

    def is_landscape(self):
        return self.aspect_ratio > HIGHEST_SQUARE_ASPECT_RATIO

    def get_year(self, year):
        THE_YEAR       = datetime.datetime(year, 1, 1, tzinfo=utc)
        THE_YEAR_END   = datetime.datetime(year, 12, 31, tzinfo=utc)
        return Photo.objects(created__gt=THE_YEAR, created__lt=THE_YEAR_END)


class WallPost(Document):
    user = ReferenceField(User, required=True)
    book = ReferenceField('Book')

    author_id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    text = StringField(max_length=255, required=True)
    comments = ListField(EmbeddedDocumentField(PhotoComment))
    tags = ListField(StringField)       # Something like "top_post", "page2_post3"
    like_count = IntField(default=0)
    score = FloatField(default=0)


class BookPage(DynamicEmbeddedDocument):
    page_type = StringField(max_length=20, required=True)    # Refers to a `Page` class so we know how to render
    # Whatever fields the page needs


class Book(Document):
    book_type = StringField(max_length=20, required=True)
    user = ReferenceField(User, required=True)
    slug_index = SequenceField()
    slug = StringField(max_length=20, required=True)
    created = DateTimeField(default=lambda: datetime.datetime.utcnow())
    run_time = FloatField()

    pages = ListField(EmbeddedDocumentField(BookPage))

    @property
    def photos(self):
        return Photo.objects(book=self)

    @property
    def friends(self):
        return FacebookFriend.objects(book=self)        # Repeated here because each book might have different scoring

    @property
    def top_friends(self):
        return FacebookFriend.objects(book=self, tags__contains=TOP_FRIEND_TAG)

    @property
    def top_20_friends(self):
        return FacebookFriend.objects(book=self, tags__contains=TOP_20_FRIEND_TAG)

    @property
    def friends_in_book(self):
        raise NotImplementedError

    @property
    def posts(self):
        return WallPost.objects(book=self)

    @property
    def top_posts(self):
        return WallPost.objects(book=self, tags__in='top_post')

    @property
    def birthday_posts(self):
        return WallPost.objects(book=self, tags__in='birthday')

    meta = {
        'indexes': ['book_type', 'user', 'slug', ['user', 'book_type']],
        'ordering': ['user', '-created']
    }

    def save(self, *args, **kwargs):
        # If no slug, assign one
        if self.slug is None:
            self.slug = short_url.encode_url(self.slug_index.generate_new_value())
        # Save
        super(Book, self).save(*args, **kwargs)


class FqlResult(Document):
    """
    Holds the results of an individual FQL query
    run for a user
    """
    user = ReferenceField(User, required=True)
    created = DateTimeField(default=lambda: datetime.datetime.utcnow())
    query_type = StringField(max_length=20, required=True)
    query = StringField(max_length=1000, required=True)
    results = DynamicField(required=True)

    meta = {
        'indexes': ['user', ('user', 'query_type'), ('user', 'query')],
        'ordering': ['user', 'query', '-created']
    }
