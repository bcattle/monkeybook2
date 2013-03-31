#!/usr/bin/env python
from flask.ext.script import Manager
from mongoengine.queryset import DoesNotExist
from monkeybook import app
from monkeybook.models import Users

manager = Manager(app)

@manager.command
def clearbryan():
    try:
        user = Users.objects.get(fb_id='1102318')
        user.delete()
        print 'User found, deleted.'
    except DoesNotExist:
        pass

if __name__ == "__main__":
    manager.run()
