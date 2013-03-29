from monkeybook import app, db
from flask.ext.security import UserMixin, RoleMixin


class Role(db.Document, RoleMixin):
    name = db.StringField(required=True, unique=True, max_length=80)
    description = db.StringField(max_length=255)

class User(db.Document, UserMixin):
    email = db.StringField(unique=True, max_length=255)
    password = db.StringField(required=True, max_length=120)
    active = db.BooleanField(default=True)
    remember_token = db.StringField(max_length=255)
    authentication_token = db.StringField(max_length=255)
    roles = db.ListField(db.ReferenceField(Role), default=[])

    @property
    def connections(self):
        return Connection.objects(user_id=str(self.id))

class Connection(db.Document):
    user_id = db.ObjectIdField()
    provider_id = db.StringField(max_length=255)
    provider_user_id = db.StringField(max_length=255)
    access_token = db.StringField(max_length=255)
    secret = db.StringField(max_length=255)
    display_name = db.StringField(max_length=255)
    profile_url = db.StringField(max_length=512)
    image_url = db.StringField(max_length=512)
    rank = db.IntField(default=1)

    @property
    def user(self):
        return User.objects(id=self.user_id).first()
