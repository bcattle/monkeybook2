import datetime
from decimal import Decimal
from flask.ext.login import UserMixin
from mongoengine import *
from monkeybook import app, db

FB_ID_FIELD_LENGTH = 30


class AccessToken(EmbeddedDocument):
    provider = StringField(max_length=255, required=True)
    access_token = StringField(max_length=255, required=True)
    secret = StringField(max_length=255, required=True)


class FamilyMember(EmbeddedDocument):
    fb_id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    relationship = StringField(max_length=10)


class FacebookFriend(EmbeddedDocument):
    fb_id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    name = StringField(max_length=255)
    first_name = StringField(max_length=50)
    gender = StringField(max_length=1)
    pic_square = StringField(max_length=255)
    top_friends_score = IntField(default=0)


class Users(Document, UserMixin):
    fb_id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    email = EmailField(unique=True, max_length=255)
    username = StringField(unique=True, max_length=255)
    active = BooleanField(default=True)
    access_tokens = EmbeddedDocumentField(AccessToken)
    locale = StringField(max_length=10)

    name = StringField(max_length=255)
    first_name = StringField(max_length=50)
    gender = StringField(max_length=1)
    pic_square = StringField(max_length=255)
    pic_square_large = StringField(max_length=255)
    friends = EmbeddedDocumentField(FacebookFriend)

    stripe_customer_id = StringField(max_length=255)
    logins = ListField(DateTimeField)

    meta = {
        'indexes': ['fb_id']
    }


class UserTasks(Document):
    user = ReferenceField(Users, required=True)
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


class Orders(Document):
    user = ReferenceField(Users, required=True)
    stripe_single_use_token = StringField(max_length=255, required=True)
    items = EmbeddedDocumentField(CartItem)
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
    fb_id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    people_in_photo = ListField(StringField)
    height = IntField(required=True)
    width = IntField(required=True)
    url = URLField(required=True)
    all_sizes = EmbeddedDocumentField(PhotoSize)
    caption = StringField(max_length=255, required=True)
    comments = EmbeddedDocumentField(PhotoComment)
    tags = ListField(StringField)
    score = IntField(default=0)

    meta = {
        'ordering': ['-score']
    }


class WallPost(EmbeddedDocument):
    author_id = StringField(unique=True, max_length=FB_ID_FIELD_LENGTH, primary_key=True)
    text = StringField(max_length=255, required=True)
    score = IntField(default=0)


class BookPage(DynamicEmbeddedDocument):
    page_type = StringField(max_length=20, required=True)    # Refers to a `Page` class so we know how to render
    # Whatever fields the page needs


class Books(Document):
    user = ReferenceField(Users, required=True)
    book_type = StringField(max_length=20, required=True)
    created = DateTimeField(default=lambda: datetime.datetime.utcnow())

    relationship_status = StringField(max_length=10)
    significant_other_id = StringField(max_length=FB_ID_FIELD_LENGTH)
    family = EmbeddedDocumentField(FamilyMember)
    friends = EmbeddedDocumentField(FacebookFriend)      # Repeated here because each book might have different scoring
    photos = EmbeddedDocumentField(Photo)
    top_posts = EmbeddedDocumentField(WallPost)
    birthday_posts = EmbeddedDocumentField(WallPost)

    pages = EmbeddedDocumentField(BookPage)

    mega = {
        'ordering': ['user', '-created']
    }


class FqlResults(Document):
    """
    Holds the results of an individual FQL query
    run for a user
    """
    user = ReferenceField(Users, required=True)
    created = DateTimeField(default=lambda: datetime.datetime.utcnow())
    query_type = StringField(max_length=20, required=True)
    query_string = StringField(max_length=1000, required=True)
    results = DynamicField(required=True)

