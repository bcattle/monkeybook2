import datetime, calendar
from pytz import utc
from monkeybook.books import Book

BOOK = Book(
    book_type='yearbook2012',
    title='2012 Yearbook',
    cover='img/book_icon_144.png',
    url_prefix='yearbook',
    module_prefix='yearbook2012',
)

YEARBOOK_YEAR   = 2012
THIS_YEAR       = datetime.datetime(YEARBOOK_YEAR, 1, 1, tzinfo=utc)
THIS_YEAR_END   = datetime.datetime(YEARBOOK_YEAR, 12, 31, tzinfo=utc)
# http://stackoverflow.com/a/11409065/1161906
UNIX_THIS_YEAR      = calendar.timegm(THIS_YEAR.utctimetuple())
UNIX_THIS_YEAR_END  = calendar.timegm(THIS_YEAR_END.utctimetuple())

GROUP_PHOTO_CUTOFF = datetime.datetime(YEARBOOK_YEAR - 2, 1, 1, tzinfo=utc)


# Does the user have enough data for the entire book?
MIN_TOP_PHOTOS_FOR_BOOK     = 10


# Photo tags
GROUP_PHOTO_TAG = 'group_photo'
# Friend tags
TOP_FRIEND_TAG      = 'top_friend'
TOP_20_FRIEND_TAG   = 'top_20_friend'


PHOTO_FIELDS = 'object_id, images, created, comment_info, like_info'
#PHOTO_WIDTH_DESIRED     = 900
PHOTO_WIDTH_DESIRED     = 565

TOP_FRIEND_POINTS_FOR_PHOTO_COMMENT = 2
TOP_FRIEND_POINTS_FOR_POST          = 3
TOP_FRIEND_POINTS_FOR_PHOTO_OF_2    = 5
TOP_FRIEND_POINTS_FOR_PHOTO_OF_3    = 3
TOP_FRIEND_POINTS_FOR_PHOTO_OF_4    = 1

TOP_PHOTO_POINTS_FOR_TOP_FRIENDS    = 3
TOP_PHOTO_POINTS_FOR_COMMENT        = 3
TOP_PHOTO_POINTS_FOR_LIKE           = 2

GROUP_PHOTO_POINTS_FOR_TOP_FRIENDS  = 3
GROUP_PHOTO_POINTS_FOR_COMMENT      = 3
GROUP_PHOTO_POINTS_FOR_LIKE         = 2

ALBUM_POINTS_FOR_TOP_PHOTO          = 2
ALBUM_POINTS_FOR_OTHER_PHOTO        = 1

COMMENT_POINTS_FOR_MADE_BY_ME       = 7
COMMENT_POINTS_FOR_COMMENT          = 5
COMMENT_POINTS_FOR_LIKE             = 1
COMMENTS_TO_PULL                    = 4
# Used in rendering yb
COMMENT_POINTS_I_LIKE               = 3

GROUP_PHOTO_IS              = 4     # How many people are in a group photo?
NUM_GROUP_PHOTOS            = 3

NUM_TOP_ALBUMS              = 3
ALBUM_PHOTOS_TO_SHOW        = 4
ALBUM_MIN_PHOTOS            = 1
ALBUMS_TO_PULL_AT_ONCE      = 10
BANNED_ALBUM_NAMES          = {'mobile uploads', 'timeline photos', 'ios photos',
                               'profile pictures', 'cover photos'}
ALBUM_POINTS_FOR_COMMENT    = 1
ALBUM_POINTS_FOR_LIKE       = 1
PICS_OF_USER_TO_PROMOTE     = 2

NUM_TOP_FRIENDS             = 5
NUM_TOP_FRIENDS_STORED      = 30
TOP_FRIEND_MIN_UNUSED_PHOTOS = 1     # If a person has fewer than this many photos, they are dsq
TOP_FRIEND_PHOTOS_TO_SHOW   = 2

RECENT_IS_YEARS             = 3
NUM_PREV_YEARS              = 7     # 2011-2005

IMMEDIATE_FAMILY            = ['mother', 'father', 'brother', 'sister']
NUM_GFBF_FAMILY_FIRST       = 2
SIGNIFICANT_OTHER_STAT      = u'That special somebody'
FAMILY_STAT                 = u'Family'

NUM_FRIENDS_IN_FACEPILE     = 90
NUM_BIRTHDAY_POSTS          = 24

LOWEST_SQUARE_ASPECT_RATIO  = 0.9        # How low can the aspect ratio be for a photo to be considered "square"?
HIGHEST_SQUARE_ASPECT_RATIO = 1.1        # How high?

PAGE_TEMPLATE_DIR           = 'pages/'
