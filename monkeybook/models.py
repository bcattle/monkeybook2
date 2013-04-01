import datetime
from decimal import Decimal
from facebook import GraphAPI
from flask.ext.login import UserMixin
from mongoengine import *

FB_ID_FIELD_LENGTH = 30


class AccessToken(EmbeddedDocument):
    provider = StringField(max_length=255, required=True)
    access_token = StringField(max_length=255, required=True)
    created = DateTimeField(default=lambda: datetime.datetime.utcnow())


class FamilyMember(EmbeddedDocument):
    id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    relationship = StringField(max_length=10)


class FacebookFriend(EmbeddedDocument):
    id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    name = StringField(max_length=255)
    first_name = StringField(max_length=50)
    sex = StringField(max_length=10)
    pic_square = StringField(max_length=255)
    top_friends_score = IntField(default=0)

    meta = {
        'indexes': ['id']
    }


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
    affiliations = ListField(DictField())
    age_range = DictField()
    location = DictField()
    pic_square = StringField(max_length=255)
    pic_square_large = StringField(max_length=255)

    relationship_status = StringField(max_length=10)
    significant_other_id = StringField(max_length=FB_ID_FIELD_LENGTH)
    friends = ListField(EmbeddedDocumentField(FacebookFriend))
    family = ListField(EmbeddedDocumentField(FamilyMember))

    stripe_customer_id = StringField(max_length=255)
    logins = ListField(DateTimeField)

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
    # created = ObjectID().getTimestamp()


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


class PhotoSize(EmbeddedDocument):
    height = IntField(required=True)
    width = IntField(required=True)
    url = URLField(required=True)


class PhotoComment(EmbeddedDocument):
    made_by = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    text = StringField(max_length=255, required=True)
    score = IntField(default=0)

    meta = {
        'ordering': ['-score']
    }


class Photo(EmbeddedDocument):
    id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    people_in_photo = ListField(StringField)
    height = IntField(required=True)
    width = IntField(required=True)
    url = URLField(required=True)
    all_sizes = ListField(EmbeddedDocumentField(PhotoSize))
    caption = StringField(max_length=255, required=True)
    comments = ListField(EmbeddedDocumentField(PhotoComment))
    tags = ListField(StringField)
    score = IntField(default=0)

    meta = {
        'indexes': ['id'],
        'ordering': ['-score']
    }


class WallPost(EmbeddedDocument):
    author_id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    text = StringField(max_length=255, required=True)
    score = IntField(default=0)


class BookPage(DynamicEmbeddedDocument):
    page_type = StringField(max_length=20, required=True)    # Refers to a `Page` class so we know how to render
    # Whatever fields the page needs


class Book(Document):
    user = ReferenceField(User, required=True)
    book_type = StringField(max_length=20, required=True)
    created = DateTimeField(default=lambda: datetime.datetime.utcnow())

    friends = ListField(EmbeddedDocumentField(FacebookFriend))      # Repeated here because each book might have different scoring
    photos = ListField(EmbeddedDocumentField(Photo))
    top_posts = ListField(EmbeddedDocumentField(WallPost))
    birthday_posts = ListField(EmbeddedDocumentField(WallPost))

    pages = ListField(EmbeddedDocumentField(BookPage))

    meta = {
        'ordering': ['user', '-created']
    }


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
