import datetime
from collections import defaultdict
from celery import group
from monkeybook import celery
from monkeybook.models import User, FacebookFriend
from monkeybook.tasks import LoggedUserTask
from monkeybook.tasks.fql import run_fql
from monkeybook.fql.top_friends import GetFriendsTask, TaggedWithMeTask
from monkeybook.utils import merge_dicts
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@celery.task(base=LoggedUserTask)
def top_friends_task(user_id):
    """
    Pulls all friends and all photo tags, combines them
    to get `top_friends_score` and saves to the `User.friends` field
    """
    # Run the child tasks
    friends_task =          run_fql.s(task_cls=GetFriendsTask, user_id=user_id)
    tagged_with_me_task =   run_fql.s(task_cls=TaggedWithMeTask, user_id=user_id)
    job_async = group([friends_task, tagged_with_me_task]).apply_async()

    results = job_async.get()
    results = merge_dicts(*results)

    all_friends = results['get_friends']
    tagged_with_me = results['tagged_with_me']

    # Collapse the tags by user_id, discount by age
    tag_score_by_user_id = defaultdict(lambda: 0.0)
    for tag in tagged_with_me.fields:
        tag_age = datetime.date.today().year - tag['created'].year + 1.0
        tag_score_by_user_id[tag['subject']] += 1 / tag_age

    # Sort
    user_ids_in_score_order = sorted(tag_score_by_user_id.items(), key=lambda x: x[1])

    # Reversing them means the index corresponds to top friends order
    top_friends_order_by_id = {}
    for top_friends_order, u in enumerate(user_ids_in_score_order):
        top_friends_order_by_id[u[0]] = top_friends_order + 1   # 0 is not a valid value

    # Copy `top_friends_order`s to `all_friends`
    for id, top_friends_order in top_friends_order_by_id.items():
        try:
            all_friends.fields_by_id[id]['top_friends_order'] = top_friends_order
        except KeyError:
            # Means you were tagged with someone you aren't friends with
            pass

    # Save
    user = User.objects.get(id=user_id)
    # Clear current friends
    FacebookFriend.objects(user=user).delete()
    # Bulk insert the new ones
    docs = []
    for friend in results['get_friends'].fields:
        uid = friend.pop('id')
        docs.append(FacebookFriend(uid=uid, user=user, **friend))
    FacebookFriend.objects.insert(docs)

    logger.info('Pulled %d friends, %d top friends for user %s'
                % (len(all_friends), len(top_friends_order_by_id), user.get_id_str()))

    return results
