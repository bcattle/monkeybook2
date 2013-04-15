from monkeybook.fql.base import FQLTask
from monkeybook.fql.getter import ResultGetter
# TODO: remove this dependency, or move this fql into Yearbook2012
from monkeybook.books.yearbook2012.settings import *


class OwnerPostsFromYearTask(FQLTask):
    fql = '''
        SELECT post_id, actor_id, created_time, comments, likes, message FROM stream
            WHERE source_id=me() AND message!='' AND filter_key='owner'
            AND created_time > %s AND created_time < %s LIMIT 500
    ''' % (UNIX_THIS_YEAR, UNIX_THIS_YEAR_END)

    def on_results(self, results):
        getter = ResultGetter(
            results,
            id_field='post_id',
            id_is_int=False,
            fields=['actor_id', 'created_time', 'comments', 'comments.count',
                    'likes.count', 'message'],
            field_names={'comments.count': 'comment_count', 'likes.count': 'like_count'},
            defaults={'comments.count': 0, 'likes.count':0 },
            timestamps=['created_time']
        )
        return getter


class OthersPostsFromYearTask(OwnerPostsFromYearTask):
    fql = '''
        SELECT post_id, actor_id, created_time, comments, likes, message FROM stream
            WHERE source_id=me() AND message!='' AND filter_key='others'
            AND created_time > %s AND created_time < %s LIMIT 500
    ''' % (UNIX_THIS_YEAR, UNIX_THIS_YEAR_END)


#class GetPostTask(FQLTask):
#    def __init__(self, post_ids, name=None):
#        self.fql = ['''
#            SELECT message, comments, likes, created_time, place, attachment
#                FROM stream WHERE post_id = '%s'
#        ''' % post_id for post_id in post_ids]
#        super(GetPostTask, self).__init__(name)
#
#    def on_results(self, results):
#        # This one requires looping through to get the comments (and likes for that matter)
#        # Just return the JSON
#        return results
