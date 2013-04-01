from monkeybook.fql.base import FQLTask
from monkeybook.models import User, FamilyMember


class ProfileFieldsTask(FQLTask):
    fql = '''
        SELECT uid, username, email, name, affiliations, age_range, current_location,
            first_name, pic_square, locale, relationship_status, sex,
            significant_other_id
            FROM user WHERE uid = me()
    '''

    def on_results(self, results):
        return results[0]

    def save(self, results):
        results.pop('uid')
        update_model(self.user, results)
        self.user.save()


def update_model(model, fields):
    for field, val in fields.items():
        setattr(model, field, val)


class FamilyTask(FQLTask):
    fql = '''
        SELECT uid, relationship FROM family WHERE profile_id = me()
    '''

    def on_results(self, results):
        return results

    def save(self, results):
        # Overwrites the existing list
        self.user.family = [FamilyMember(id=str(f['uid']), relationship=f['relationship'])
                            for f in results]
        self.user.save()


class SquareProfilePicTask(FQLTask):
    fql = '''
        SELECT url,real_size FROM square_profile_pic WHERE id = me() AND size = 160
    '''

    def on_results(self, results):
        return results[0]

    def save(self, results):
        self.user.pic_square_large = results['url']
        self.user.save()

