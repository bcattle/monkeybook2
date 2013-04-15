import time, itertools
from collections import defaultdict, Counter
from celery import group
from monkeybook import celery
from monkeybook.models import Book, Photo, PhotoSize, PhotoComment, WallPost, FacebookFriend
from monkeybook.tasks import LoggedUserTask
from monkeybook.tasks.fql import run_fql, get_result_or_run_fql
from monkeybook.fql.getter import FreqDistResultGetter, ResultGetter
from monkeybook.fql.photos import PhotosOfMeTask, CommentsOnPhotosOfMeTask
from monkeybook.fql.posts import OwnerPostsFromYearTask, OthersPostsFromYearTask
from monkeybook.fql.top_friends import GetFriendsTask, TaggedWithMeTask
from monkeybook.fql.profile import FamilyTask
from monkeybook.books.yearbook2012.settings import *
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def get_comment_score(comment):
    score = \
        COMMENT_POINTS_I_LIKE * comment['likes'] + \
        COMMENT_POINTS_FOR_LIKE * (1 if comment['user_likes'] else 0)
    return score


def save_photos_and_tags(user, book, tagged_with_me, comments_on_photos_of_me, photos_of_me):
    # Toss any results in 'tagged_with_me' that aren't in 'photos_of_me'
    tagged_with_me = tagged_with_me.filter(
        lambda x: x['object_id'] in photos_of_me.ids
    )

    # Get number of people in each photo
    # num_tags_by_photo_id = FreqDistResultGetter(tagged_with_me, id_field='object_id')

    # Get list of people in each photo
    tags_by_user_id = defaultdict(list)
    tagged_people_by_photo_id = defaultdict(list)
    for tag in tagged_with_me:
        tagged_people_by_photo_id[tag['object_id']].append(tag['subject'])
        tags_by_user_id[tag['subject']].append(tag)

    comments_by_photo_id = defaultdict(list)
    comments_score_by_user_id = defaultdict(lambda: 0)
    for comment in comments_on_photos_of_me:
        # Get the comments in each photo
        comments_by_photo_id[comment['object_id']].append(comment)

        # Get the number of commments by each user, discounted by year
        comments_score_by_user_id[comment['fromid']] += \
            TOP_FRIEND_POINTS_FOR_PHOTO_COMMENT / max((THIS_YEAR.year - comment['time'].year + 1.0), 1.0)

    # Save the photos to the database
    db_photos_by_id = {}
    for photo in photos_of_me:
        photo_db = Photo(
            id      = photo['id'],
            user    = user,
            book    = book,

            created             = photo['created'],
            people_in_photo     = tagged_people_by_photo_id[photo['id']],
            height              = photo['height'],
            width               = photo['width'],
            url                 = photo['fb_url'],
            all_sizes           = [PhotoSize(**size) for size in photo['all_sizes']],
            caption             = photo['caption'],

            comments    = [PhotoComment(
                made_by = comment['fromid'],
                created = comment['time'],
                text = comment['text'],
                score = get_comment_score(comment),
                likes = comment['likes'],
                user_likes = comment['user_likes'],
            ) for comment in comments_by_photo_id[photo['id']] if comment],     # it's a defaultdict
        )
        db_photos_by_id[photo['id']] = photo_db
    Photo.insert(db_photos_by_id.items())

    # Save the tags to the database
    for user_id, tags in tags_by_user_id.items():
        book.friends.get(uid=user_id).update(tagged_in_photos__push_all=tags)
        # FacebookFriend.objects(book=book, uid=user_id).update(tagged_in_photos__push_all=tags)

    results = {
        'db_photos_by_id':           db_photos_by_id,
        'comments_score_by_user_id': comments_score_by_user_id,
    }
    return results


def calculate_top_friends(user, book,
                          others_posts_from_year, owner_posts_from_year, db_photos_by_id,
                          photos_of_me, comments_score_by_user_id):

    # Combine the lists of posts
    all_posts_this_year = ResultGetter.from_fields(itertools.chain(
        others_posts_from_year,
        owner_posts_from_year
    ))

    # Strip posts that have an attachment that is a photo?
    #    .filter(lambda x: 'attachment' in x and 'fb_object_type' in x['attachment'] and x['attachment'])

    # Assign each friend points for each post they made
    posts_score_by_user_id = defaultdict(lambda: 0)
    for post in all_posts_this_year:
        # if 'score' not in post:
        #     post['score'] = 0
        # post['score'] += TOP_FRIEND_POINTS_FOR_POST
        posts_score_by_user_id[post['actor_id']] += TOP_FRIEND_POINTS_FOR_POST

    # Calculate photo score for each user, discounted by year
    photos_score_by_user_id = defaultdict(lambda: 0.0)
    # tagged_friends = FacebookFriend.objects(user=user, book=book, tagged_in_photos__exists=True)    # they have at least one tag
    for friend in book.friends:
        for tag in friend.tagged_in_photos:
            photo_id = tag['object_id']
            peeps_in_photo = db_photos_by_id[photo_id].num_people_in_photo
            photo = photos_of_me.fields_by_id[photo_id]
            #            photo_age = 2012 - photo['created'].year + 1.0
            photo_age = datetime.date.today().year - photo['created'].year + 1.0
            if peeps_in_photo == 2:
                photos_score_by_user_id[friend.uid] += TOP_FRIEND_POINTS_FOR_PHOTO_OF_2 / photo_age
            elif peeps_in_photo == 3:
                photos_score_by_user_id[friend.uid] += TOP_FRIEND_POINTS_FOR_PHOTO_OF_3 / photo_age
            elif peeps_in_photo >= 4:
                photos_score_by_user_id[friend.uid] += TOP_FRIEND_POINTS_FOR_PHOTO_OF_4 / photo_age

    # Add em up
    top_friend_ids = (set(comments_score_by_user_id.keys()) | set(posts_score_by_user_id.keys())
                      | set(photos_score_by_user_id))
    top_friend_ids.remove(user.profile.facebook_id)

    # Tag the users in the database and update their score
    for user_id in top_friend_ids:
        FacebookFriend.objects(book=book, uid=user_id).update(
            top_friends_score=comments_score_by_user_id[user_id] + posts_score_by_user_id[user_id]
                              + photos_score_by_user_id[user_id],
            comments_score=comments_score_by_user_id[user_id],
            posts_score=posts_score_by_user_id[user_id],
            photos_score=photos_score_by_user_id[user_id],
            tags__push=TOP_FRIEND_TAG
        )

    # Grab the top 20 users and give them an additional tag
    for top_20_user in book.friends.order_by('-top_friends_score')[:20]:
        top_20_user.update(tags__push=TOP_20_FRIEND_TAG)

    # Cache a list of the friends by id
    db_friends_by_id = {friend.uid: friend for friend in book.friends}

    results = {
        'all_posts_this_year': all_posts_this_year,
        'db_friends_by_id': db_friends_by_id,
    }
    return results


def calculate_photo_scores(book):

    friend_ids = set(book.friends.scalar('uid'))
    top_friend_ids = set(book.top_friends.scalar('uid'))
    top_20_friend_ids = set(book.top_20_friends.scalar('uid'))

    for photo in book.photos:

        # For each photo, get the number of top friends in the photo
        friends_in_photo = set(photo.people_in_photo)
        top_friends_in_photo = friends_in_photo & top_friend_ids
        top_20_friends_in_photo = friends_in_photo & top_20_friend_ids

        photo.num_top_friends_in_photo = len(top_friends_in_photo)
        photo.num_top_20_friends_in_photo = len(top_20_friends_in_photo)

        # How many comments by friends of mine?
        photo.comments_from_friends = 0
        for comment in photo.comments:
            if comment.fromid in friend_ids:
                photo.comments_from_friends += 1

        # Calculate the score
        photo.score = (
            (TOP_PHOTO_POINTS_FOR_TOP_FRIENDS * photo.top_friends_points +
                  TOP_PHOTO_POINTS_FOR_COMMENT * photo.comments_from_friends +
                  TOP_PHOTO_POINTS_FOR_LIKE * photo.like_count) /
                     max(photo.num_people_in_photo - 2.0, 1.0)
        )
        photo.save()



def calculate_top_group_photo_scores(book):
    # group_photos_this_year is only 1 for me
    group_photos = book.photos.filter(created__gt=GROUP_PHOTO_CUTOFF).filter(__raw__= {
        'people_in_photo': {'$exists': 1},
        '$where': 'this.people_in_photo.length >= %d' % GROUP_PHOTO_IS
    })

    # Assign the group photo score
    for photo in group_photos:
        group_photo_score = GROUP_PHOTO_POINTS_FOR_TOP_FRIENDS * photo.num_top_friends_in_photo + \
                            GROUP_PHOTO_POINTS_FOR_COMMENT * len(photo.comments) + \
                            GROUP_PHOTO_POINTS_FOR_LIKE * photo.like_count
                            # or only count `comments_from_friends`
        photo.update(group_photo_score=group_photo_score)



def calculate_top_albums(photos_of_me):
    album_score_and_date_by_id = defaultdict(lambda: {'score': 0, 'created': None})
    for photo in photos_of_me:
        album_score_and_date_by_id[photo['album_object_id']]['score'] += photo['score']
        # Also tag with the date
        album_score_and_date_by_id[photo['album_object_id']]['created'] = photo['created']

    return album_score_and_date_by_id


def assign_post_scores(book):
    top_friend_ids = set(book.top_friends.scalar('uid'))

    for post in book.posts:
        top_friend_comments = 0
        for comment in post.comments:
            if comment.fromid in top_friend_ids:
                top_friend_comments += 1
        post_score = \
            (COMMENT_POINTS_FOR_MADE_BY_ME * 1 if post.author_id == book.user.id else 0) + \
            COMMENT_POINTS_FOR_COMMENT * top_friend_comments + \
            COMMENT_POINTS_FOR_LIKE * post.like_count

        post.update(score=post_score)


def get_birthday_posts(book):
    if book.user.birthday:
        birthday_posts = []
        birth_date = book.user.birthday
        birthday_this_year = datetime.datetime(2012, birth_date.month, birth_date.day, 0, 0, 0, tzinfo=utc)
        start_time = birthday_this_year - datetime.timedelta(days=1)
        end_time = birthday_this_year + datetime.timedelta(days=3)
        birthday_posts = all_posts_this_year.filter(
            lambda x: start_time < x['created_time'] < end_time and x['message'] and x['actor_id'] in get_friends.ids
        )
    # Add the tag 'birthday_post'

@celery.task(base=LoggedUserTask)
def run_book(user):
    """
    The overall philosophy here is that ----
        - these functions annotate the data
        - the page classes read the annotations and "claim" photos
    """
    runtime_start = time.time()

    # Create the book
    book = Book(user=user, book_type=BOOK.book_type)

    # Run separate, async tasks to facebook
    fql_job = group([
        run_fql.s(kwargs={'task_cls': PhotosOfMeTask,           'user_id': user.id}),
        run_fql.s(kwargs={'task_cls': CommentsOnPhotosOfMeTask, 'user_id': user.id}),
        run_fql.s(kwargs={'task_cls': OwnerPostsFromYearTask,   'user_id': user.id}),
        run_fql.s(kwargs={'task_cls': OthersPostsFromYearTask,  'user_id': user.id}),
    ])
    job_async = fql_job.apply_async()

    # family_async = run_fql.s(task_cls=FamilyTask, user_id=user.id, commit=True).apply_async()
    family_async = run_fql.delay(task_cls=FamilyTask, user_id=user.id, commit=True)

    # While that's running, collect the other dependent tasks
    friends_task_async =        get_result_or_run_fql.s(task_cls=GetFriendsTask, user_id=user.id)
    tagged_with_me_task_async = get_result_or_run_fql.s(task_cls=TaggedWithMeTask, user_id=user.id)

    results = job_async.get()
    results['get_friends'] = friends_task_async.get()
    results['tagged_with_me'] = tagged_with_me_task_async.get()

    ## Results contains
    get_friends              = results['get_friends']       # --> all friends     (already saved to db)
    tagged_with_me           = results['tagged_with_me']    # --> `subject, object_id, created` from tags of photos I am in
    comments_on_photos_of_me = results['comments_on_photos_of_me']
    others_posts_from_year   = results['others_posts_from_year']
    owner_posts_from_year    = results['owner_posts_from_year']
    photos_of_me             = results['photos_of_me']

    ## Save all the photos
    results = save_photos_and_tags(user, book, tagged_with_me, comments_on_photos_of_me, photos_of_me)

    db_photos_by_id = results['db_photos_by_id']
    comments_score_by_user_id = results['comments_score_by_user_id']

    ## If they don't have enough photos this year, bail out of the yearbook process

    if Photo.objects(book=book).get_year(YEARBOOK_YEAR).count() < MIN_TOP_PHOTOS_FOR_BOOK:
        celery.current_task.update_state(state='NOT_ENOUGH_PHOTOS')
        # This is a hack because celery overwrites the task state when you return
        # could also use an `after_return` handler, see http://bit.ly/16U6YKv
        return 'NOT_ENOUGH_PHOTOS'

    ## Calculate top friends
    results = calculate_top_friends(user, book,
                                    others_posts_from_year, owner_posts_from_year, db_photos_by_id,
                                    photos_of_me, comments_score_by_user_id)

    all_posts_this_year = results['all_posts_this_year']
    db_friends_by_id    = results['db_friends_by_id']

    ## Save all posts
    db_posts = []
    for post in all_posts_this_year:
        db_posts.append(WallPost(user=user, book=book, **post))
    WallPost.insert(db_posts)

    ## Score all the photos
    calculate_photo_scores(book)

    ## Calculate top group photos
    calculate_top_group_photo_scores(book)


    ## Calculate top albums
    album_score_and_date_by_id = calculate_top_albums(photos_of_me)

    ## Assign post scores
    assign_post_scores(book)

    ## Pull out birthday posts
    birthday_posts = get_birthday_posts(book)

    ## Go through and add tags to the photo objects
    ##    tags indicate membership in a category - group_photo
    ##    tags may also relate to a (new) score field - group_photo_score


    # We run the pages one by one. They run in order of preference (not necessarily book order)
    # Each page has a inclusion criteria, and a assignment function


    # Back in time
    max_year, photos_of_me_by_year = results['photos_of_me'].bucket_by_year()
    years = list(sorted(photos_of_me_by_year.keys(), reverse=True))
    back_in_time = []
    for index, year in enumerate(years[1:NUM_PREV_YEARS + 1]):
        year_photo_ids = []
        for photo in photos_of_me_by_year[year].order_by('score'):
            year_photo_ids.append(photo['id'])
        back_in_time.append(year_photo_ids)
    rankings.back_in_time = back_in_time

    ## Assign photos to the Yearbook, avoiding duplicates
    #    try:
    #        old_yb = Yearbook.objects.get(rankings=rankings)
    #        old_yb.delete()
    #    except Yearbook.DoesNotExist: pass

    yb.top_post = 0
    yb.birthday_posts = birthday_posts.fields

    yb.top_photo_1 = yb.get_first_unused_photo_landscape(rankings.top_photos)           # landscape
    yb.top_photo_2 = yb.get_first_unused_photo(rankings.top_photos)
    yb.top_photo_3 = yb.get_first_unused_photo(rankings.top_photos)
    yb.top_photo_4 = yb.get_first_unused_photo(rankings.top_photos)
    yb.top_photo_5 = yb.get_first_unused_photo(rankings.top_photos)

    # `assign_group_photos` uses FacebookPhoto classes to determine portrait/landscape
    # make sure they finished saving to the db
    # print 'save_to_db state: %s' % save_to_db_async.state
    save_to_db_async.get()

    # Assign the group photos from different albums, if possible
    # Make one pass assigning from different albums,
    # then a second filling in the gaps
    #    assigned_group_photos = assign_group_photos(yb, rankings, results['photos_of_me'], do_unique_albums=True)
    #    if assigned_group_photos < NUM_GROUP_PHOTOS:
    #        assign_group_photos(yb, rankings, results['photos_of_me'], do_unique_albums=False)

    ## Top friends
    # Do this after we assign the top photos and top group photos,
    # so we can make sure there are enough unused photos of them

    # We need to make sure the user exists in the db
    # Users that came back from the db are still in results['get_friends']
    saved_friends_ids = results['get_friends'].ids

    # Make sure the family task finished running
    family_async.get()
    # Need to re-sync `user`?
    family_ids = user.family.all().values_list('facebook_id', flat=True)
    top_friend_ids = []
    gfbf_added = False
    for user_id, score in sorted(top_friend_score_by_id.items(), key=lambda x: x[1], reverse=True):
        if yb.num_unused_photos(tags_by_user_id[user_id]) >= TOP_FRIEND_MIN_UNUSED_PHOTOS and user_id in saved_friends_ids:
            # If user is family or gfbf, insert at front
            if user_id == user.profile.significant_other_id:
                top_friend_ids.insert(0, user_id)
                gfbf_added = True
            elif user_id in family_ids:
                top_friend_ids.insert(1 if gfbf_added else 0, user_id)
            else:
                top_friend_ids.append(user_id)

    # Need to build another list that combines tag and photo score
    rankings.top_friends_ids = top_friend_ids[:NUM_TOP_FRIENDS_STORED]
    top_friends_photos = []
    for friend_id in top_friend_ids:
        friend_tags = tags_by_user_id[friend_id]
        top_friend_photos = []
        for tag in friend_tags:
            tag_id = tag['object_id']
            photo = results['photos_of_me'].fields_by_id[tag_id]
            top_friend_photos.append({'id': tag_id, 'score': top_photo_score_by_id[tag_id],
                                      'width': photo['width'], 'height': photo['height']})
        top_friend_photos.sort(key=lambda x: x['score'], reverse=True)
        top_friends_photos.append(top_friend_photos)
    rankings.top_friends_photos = top_friends_photos

    ## Assign the top friends
    #    used_albums = []
    for index in range(min(NUM_TOP_FRIENDS, len(top_friend_ids))):
        # Index
        setattr(yb, 'top_friend_%d' % (index + 1), index)
        # Friend stat
        if top_friend_ids[index] == user.profile.significant_other_id:
            friend_stat = SIGNIFICANT_OTHER_STAT
        elif top_friend_ids[index] in family_ids:
            friend_stat = FAMILY_STAT
        else:
            num_tags = len(rankings.top_friends_photos[index])
            friend_stat = u'Tagged in %d photo%s with you' % (num_tags, 's' if num_tags > 1 else '')
        setattr(yb, 'top_friend_%d_stat' % (index + 1), friend_stat)
        # Set photo
        #        tf_photo_index = yb.get_first_unused_photo(rankings.top_friends_photos[index])
        tf_photo_index = yb.get_first_unused_photo_landscape(rankings.top_friends_photos[index])
        setattr(yb, 'top_friend_%d_photo_1' % (index + 1), tf_photo_index)
        # If photo was portrait, grab another one
    #        tf_photo_id = rankings.top_friends_photos[index][tf_photo_index]['id']
    #        tf_photo = results['photos_of_me'].fields_by_id[tf_photo_id]
    #        if tf_photo['width'] / float(tf_photo['height']) < HIGHEST_SQUARE_ASPECT_RATIO:
    #            tf_photo_index_2 = yb.get_first_unused_photo(rankings.top_friends_photos[index])
    #            setattr(yb, 'top_friend_%d_photo_2' % (index + 1), tf_photo_index_2)

    ## Top albums

    # Start pulling album names, photos
    # Can't pickle defaultdict? so just call it here, wouldn't save us much time anyway
    #    pull_albums_async = pull_album_photos.delay(user, album_score_and_date_by_id)
    #    album_photos_by_score, albums_ranked = pull_albums_async.get()
    album_photos_by_score, albums_ranked = pull_album_photos(user, album_score_and_date_by_id)
    rankings.top_albums_photos = album_photos_by_score
    rankings.top_albums_ranked = albums_ranked

    albums_assigned = 0
    all_top_albums = rankings.top_albums_photos[:]
    curr_album_index = -1
    while all_top_albums:
        curr_album = all_top_albums.pop(0)
        curr_album_index += 1
        photos_to_show = []
        no_more_pics_of_user = False
        while True:
            if len(photos_to_show) < PICS_OF_USER_TO_PROMOTE and not no_more_pics_of_user:
                # Want a pic of the user, loop through album photos looking for one
                photo_of_user = get_next_unused_photo_of_user(
                    yb,
                    curr_album,
                    results['photos_of_me'],
                    used_indices=photos_to_show
                )
                if photo_of_user:
                    photos_to_show.append(photo_of_user)
                else:
                    # No more pics of user, just take the next highest unused photo
                    no_more_pics_of_user = True
            else:
                next_photo = yb.get_first_unused_photo(curr_album, used_indices=photos_to_show)
                if next_photo is not None:
                    photos_to_show.append(next_photo)
                else:
                    # No photos left, break
                    break
            if len(photos_to_show) >= ALBUM_PHOTOS_TO_SHOW:
                break
        if len(photos_to_show) < ALBUM_MIN_PHOTOS:
            # Didn't have enough photos, try the next album
            continue

        # Save the fields
        album_str = 'top_album_%d' % (albums_assigned + 1)
        setattr(yb, album_str, curr_album_index)
        for field_num in range(len(photos_to_show)):
            setattr(yb, album_str + '_photo_%d' % (field_num + 1), photos_to_show[field_num])
        albums_assigned += 1
        if albums_assigned >= NUM_TOP_ALBUMS:
            break

    ## Throughout the year photos

    yb.year_photo_1 = yb.get_first_unused_photo_landscape(rankings.top_photos)
    yb.year_photo_2 = yb.get_first_unused_photo(rankings.top_photos)
    yb.year_photo_6 = get_unused_if_portrait(yb.year_photo_2, rankings.top_photos, yb, results['photos_of_me'])
    yb.year_photo_3 = yb.get_first_unused_photo(rankings.top_photos)
    yb.year_photo_7 = get_unused_if_portrait(yb.year_photo_3, rankings.top_photos, yb, results['photos_of_me'])
    yb.year_photo_4 = yb.get_first_unused_photo(rankings.top_photos)
    yb.year_photo_8 = get_unused_if_portrait(yb.year_photo_4, rankings.top_photos, yb, results['photos_of_me'])
    yb.year_photo_5 = yb.get_first_unused_photo(rankings.top_photos)
    yb.year_photo_9 = get_unused_if_portrait(yb.year_photo_5, rankings.top_photos, yb, results['photos_of_me'])

    ## Back in time photos

    years_to_show = []
    for year_index, year in enumerate(back_in_time):
        curr_year_unused = yb.get_first_unused_photo(year)
        if curr_year_unused is None:
            continue
        years_to_show.append({'year_index': year_index, 'photo_index': curr_year_unused})
        if len(years_to_show) > NUM_PREV_YEARS:
            break

    # Special case: if only found one year, pull an additional photo from that year
    if len(years_to_show) == 1:
        that_year_index = years_to_show[0]['year_index']
        unused_photo_2 = yb.get_first_unused_photo(back_in_time[that_year_index])
        if unused_photo_2 is not None:
            years_to_show.append({'year_index': that_year_index, 'photo_index': unused_photo_2})

    # Save
    for year_num in range(len(years_to_show)):
        field_str = 'back_in_time_%d' % (year_num + 1)
        setattr(yb, field_str, years_to_show[year_num]['year_index'])
        setattr(yb, field_str + '_photo_1', years_to_show[year_num]['photo_index'])

    # Tabulate the list of all friends tagged in the book and store
    all_photos = yb._get_all_used_ids()
    all_tagged_people = itertools.chain(*[
        tagged_people_by_photo_id[photo_id] for photo_id in all_photos
    ])
    tagged_people_count = Counter(all_tagged_people)
    yb.friends_in_book = tagged_people_count.most_common()

    # Update the photos
    Photo.insert(db_photos_by_id.items())

    # Save the book
    book.run_time = time.time() - runtime_start
    book.save()

    # Log the yearbook run time to mixpanel
    tracker.delay('Book Created', properties={
        'distinct_id': user.username,
        'mp_name_tag': user.username,
        'time': time.time(),
        'Book': 'Yearbook 2012',
        'Run Time (sec)': '%.1f' % yb.run_time
    })

    # Initiate a task to start downloading user's yearbook phointos?
    return book

#    except FacebookSSLError, exc:
#        logger.error('run_yearbook: FacebookSSLError, retrying.')
#        raise self.retry(exc=exc)


def get_unused_if_portrait(photo_index, photo_list, yearbook, photos_of_me):
    if photo_index is None:
        return None
    photo_id = yearbook._get_id_from_dict_or_int(photo_list[photo_index])
    photo = photos_of_me.fields_by_id[photo_id]
    if photo['width'] / float(photo['height']) < HIGHEST_SQUARE_ASPECT_RATIO:
        return yearbook.get_first_unused_photo(photo_list)
    return None


def get_next_unused_photo_of_user(yearbook, photo_list, photos_of_me, used_indices=None):
    used_indices = used_indices or []
    list_to_loop = photo_list.items() if hasattr(photo_list, 'items') else photo_list
    for photo_index, photo in enumerate(list_to_loop):
        if photo_index in used_indices:
            continue
        photo_id = photo['id'] if hasattr(photo, 'keys') else photo
        is_used = yearbook.photo_is_used(photo)
        of_me = photo_id in photos_of_me.ids
        if not is_used and of_me:
            return photo_index
    return None


def assign_group_photos(yearbook, rankings, photos_of_me, do_unique_albums=False):
    assigned_group_photos = 0
    assigned_album_ids = []
    skipped_photo_indices = []
    photo_index = None
    while True:
        if not assigned_group_photos:
            # The first photo should be landscape
            photo_index, photo_id = yearbook.get_first_unused_photo_landscape(rankings.group_shots, return_id=True)
        if assigned_group_photos > 0 or photo_index is None:
            # Subsequent iterations or it failed
            photo_index, photo_id = yearbook.get_first_unused_photo(rankings.group_shots, used_indices=skipped_photo_indices, return_id=True)
        if photo_index is not None:
            if do_unique_albums:
                # Do we already have a photo from this album?
                album_id = photos_of_me.fields_by_id[photo_id]['album_object_id']
                if album_id in assigned_album_ids:
                    # Assign the photo id to the "skipped" list
                    skipped_photo_indices.append(photo_index)
                    continue
                else:
                    assigned_album_ids.append(album_id)
                # Actually assign the photo
            setattr(yearbook, 'group_photo_%d' % (assigned_group_photos + 1), photo_index)
            assigned_group_photos += 1
        if assigned_group_photos >= NUM_GROUP_PHOTOS or photo_index is None:
            # We have enough or no unused photo, roll on
            break
    return assigned_group_photos

