# Django settings for kitsune project.
from datetime import date
import logging
import os
import platform

from sumo_locales import LOCALES

DEBUG = True
TEMPLATE_DEBUG = DEBUG
STAGE = False

LOG_LEVEL = logging.INFO
SYSLOG_TAG = 'http_sumo_app'

ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

ROOT_PACKAGE = os.path.basename(ROOT)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'kitsune',  # Or path to database file if using sqlite3.
        'USER': '',  # Not used with sqlite3.
        'PASSWORD': '',  # Not used with sqlite3.
        'HOST': '',  # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',  # Set to empty string for default. Not used with sqlite3.
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
    }
}

DATABASE_ROUTERS = ('multidb.PinningMasterSlaveRouter',)

# Put the aliases for your slave databases in this list
SLAVE_DATABASES = []

# Cache Settings
#CACHE_BACKEND = 'caching.backends.memcached://localhost:11211'
#CACHE_PREFIX = 'sumo:'

# Addresses email comes from
DEFAULT_FROM_EMAIL = 'notifications@support.mozilla.com'
SERVER_EMAIL = 'server-error@support.mozilla.com'

PLATFORM_NAME = platform.node()

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'US/Pacific'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

# Supported languages
SUMO_LANGUAGES = (
    'ak', 'ar', 'as', 'ast', 'bg', 'bn-BD', 'bn-IN', 'bs', 'ca', 'cs', 'da',
    'de', 'el', 'en-US', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fr', 'fur',
    'fy-NL', 'ga-IE', 'gd', 'gl', 'gu-IN', 'he', 'hi-IN', 'hr', 'hu', 'hy-AM',
    'id', 'ilo', 'is', 'it', 'ja', 'kk', 'kn', 'ko', 'lt', 'mai', 'mk', 'mn',
    'mr', 'ms', 'my', 'nb-NO', 'nl', 'no', 'pa-IN', 'pl', 'pt-BR',
    'pt-PT', 'rm', 'ro', 'ru', 'rw', 'si', 'sk', 'sl', 'sq', 'sr-CYRL',
    'sr-LATN', 'sv-SE', 'ta-LK', 'te', 'th', 'tr', 'uk', 'vi', 'zh-CN',
    'zh-TW',
)

LANGUAGE_CHOICES = tuple([(i, LOCALES[i].native) for i in SUMO_LANGUAGES])
LANGUAGES = dict([(i.lower(), LOCALES[i].native) for i in SUMO_LANGUAGES])

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in SUMO_LANGUAGES])

# Locales that are known but unsupported. Keys are the locale, values are
# an optional fallback locale, or None, to use the LANGUAGE_CODE.
NON_SUPPORTED_LOCALES = {
    'af': None,
    'br': 'fr',
    'csb': 'pl',
    'nb-NO': 'no',
    'nn-NO': 'no',
    'oc': 'fr',
    'sr': 'sr-CYRL',  # Override the tendency to go sr->sr-LATN.
}

TEXT_DOMAIN = 'messages'

SITE_ID = 1


# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

# Use the real robots.txt?
ENGAGE_ROBOTS = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Paths that don't require a locale prefix.
SUPPORTED_NONLOCALES = ('media', 'admin', 'robots.txt', 'services', '1',
                        'postcrash', 'wafflejs')

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#%tc(zja8j01!r#h_y)=hy!^k)9az74k+-ib&ij&+**s3-e^_z'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'session_csrf.context_processor',

    'django.contrib.messages.context_processors.messages',

    'sumo.context_processors.global_settings',
    'sumo.context_processors.for_data',
    'jingo_minify.helpers.build_ids',
    'messages.context_processors.unread_message_count',
)

MIDDLEWARE_CLASSES = (
    'multidb.middleware.PinningRouterMiddleware',
    'users.middleware.StaySecureMiddleware',
    'commonware.response.middleware.GraphiteMiddleware',
    'commonware.request.middleware.SetRemoteAddrFromForwardedFor',

    # This gives us atomic success or failure on multi-row writes. It does not
    # give us a consistent per-transaction snapshot for reads; that would need
    # the serializable isolation level (which InnoDB does support) and code to
    # retry transactions that roll back due to serialization failures. It's a
    # possibility for the future. Keep in mind that memcache defeats
    # snapshotted reads where we don't explicitly use the "uncached" manager.
    'django.middleware.transaction.TransactionMiddleware',

    # LocaleURLMiddleware must be before any middleware that uses
    # sumo.urlresolvers.reverse() to add locale prefixes to URLs:
    'sumo.middleware.LocaleURLMiddleware',

    # Mobile detection should happen in Zeus.
    'mobility.middleware.DetectMobileMiddleware',
    'mobility.middleware.XMobileMiddleware',

    'sumo.middleware.Forbidden403Middleware',
    'django.middleware.common.CommonMiddleware',
    'sumo.middleware.RemoveSlashMiddleware',
    'inproduct.middleware.EuBuildMiddleware',
    'sumo.middleware.NoCacheHttpsMiddleware',
    'commonware.middleware.NoVarySessionMiddleware',
    'commonware.middleware.FrameOptionsHeader',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sumo.anonymous.AnonymousIdentityMiddleware',
    'session_csrf.CsrfMiddleware',
    'twitter.middleware.SessionMiddleware',
    'sumo.middleware.PlusToSpaceMiddleware',
    'commonware.middleware.ScrubRequestOnException',
    'django_arecibo.middleware.AreciboMiddlewareCelery',
    'commonware.response.middleware.GraphiteRequestTimingMiddleware',
)

# Auth
AUTHENTICATION_BACKENDS = (
    'users.backends.Sha256Backend',
)
AUTH_PROFILE_MODULE = 'users.Profile'
USER_AVATAR_PATH = 'uploads/avatars/'
DEFAULT_AVATAR = MEDIA_URL + 'img/avatar.png'
AVATAR_SIZE = 48  # in pixels
MAX_AVATAR_FILE_SIZE = 131072  # 100k, in bytes
GROUP_AVATAR_PATH = 'uploads/groupavatars/'

ACCOUNT_ACTIVATION_DAYS = 30

PASSWORD_BLACKLIST = path('configs/password-blacklist.txt')

ROOT_URLCONF = '%s.urls' % ROOT_PACKAGE

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path('templates'),
)

# TODO: Figure out why changing the order of apps (for example, moving taggit
# higher in the list) breaks tests.
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'users',
    'tower',
    'jingo_minify',
    ROOT_PACKAGE,
    'authority',
    'timezones',
    'waffle',
    'access',
    'sumo',
    'search',
    'forums',
    'djcelery',
    'cronjobs',
    'tidings',
    'activity',
    'questions',
    'adminplus',
    'kadmin',
    'taggit',
    'flagit',
    'upload',
    'product_details',
    'wiki',
    'kbforums',
    'dashboards',
    'gallery',
    'customercare',
    'twitter',
    'chat',
    'inproduct',
    'postcrash',
    'landings',
    'announcements',
    'messages',
    'commonware.response.cookies',
    'groups',
    'karma',

    # Extra apps for testing.
    'django_nose',
    'test_utils',
)

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'

def JINJA_CONFIG():
    import jinja2
    from django.conf import settings
    from caching.base import cache
    config = {'extensions': ['tower.template.i18n', 'caching.ext.cache',
                             'jinja2.ext.with_'],
              'finalize': lambda x: x if x is not None else ''}
    if (hasattr(cache, 'scheme') and 'memcached' in cache.scheme and
        not settings.DEBUG):
        # We're passing the _cache object directly to jinja because
        # Django can't store binary directly; it enforces unicode on it.
        # Details: http://jinja.pocoo.org/2/documentation/api#bytecode-cache
        # and in the errors you get when you try it the other way.
        bc = jinja2.MemcachedBytecodeCache(cache._cache,
                                           "%sj2:" % settings.CACHE_PREFIX)
        config['cache_size'] = -1  # Never clear the cache
        config['bytecode_cache'] = bc
    return config

# Let Tower know about our additional keywords.
# DO NOT import an ngettext variant as _lazy.
TOWER_KEYWORDS = {
    '_lazy': None,
}

# Tells the extract script what files to look for l10n in and what function
# handles the extraction.  The Tower library expects this.
DOMAIN_METHODS = {
    'messages': [
        ('vendor/**', 'ignore'),
        ('apps/forums/**', 'ignore'),
        ('apps/questions/**', 'ignore'),
        ('apps/chat/**', 'ignore'),
        ('apps/**.py',
            'tower.management.commands.extract.extract_tower_python'),
        ('**/templates/**.html',
            'tower.management.commands.extract.extract_tower_template'),
    ],
    'lhtml': [
        ('apps/forums/**', 'ignore'),
        ('apps/questions/**', 'ignore'),
        ('**/templates/**.lhtml',
            'tower.management.commands.extract.extract_tower_template'),
    ],
    'javascript': [
        # We can't say **.js because that would dive into any libraries.
        ('media/js/*.js', 'javascript'),
    ],
}

# These domains will not be merged into messages.pot and will use separate PO
# files. See the following URL for an example of how to set these domains
# in DOMAIN_METHODS.
# http://github.com/jbalogh/zamboni/blob/d4c64239c24aa2f1e91276909823d1d1b290f0ee/settings.py#L254
STANDALONE_DOMAINS = [
    'javascript',
    ]

# If you have trouble extracting strings with Tower, try setting this
# to True
TOWER_ADD_HEADERS = True

# Bundles for JS/CSS Minification
MINIFY_BUNDLES = {
    'css': {
        'common': (
            'css/reset.css',
            'global/headerfooter.css',
            'css/kbox.css',
            'css/main.css',
        ),
        'print': (
            'css/print.css',
        ),
        # TODO: remove dependency on jquery ui CSS and use our own
        'jqueryui/jqueryui': (
            'css/jqueryui/jqueryui.css',
        ),
        'forums': (
            'css/forums.css',
        ),
        'questions': (
            'css/to-delete.css',
            'css/questions.css',
            'css/tags.css',
            'css/search.css',
        ),
        'search': (
            'css/search.css',
            'css/search-advanced.css',
        ),
        'wiki': (
            'css/users.autocomplete.css',
            'css/users.list.css',
            'css/showfor.css',
            'css/wiki.css',
            'css/wiki_syntax.css',
            # The dashboard app uses the wiki bundle because only the wiki app
            # has the new theme at the moment.
            'css/dashboards.css',
            'css/screencast.css',
            'css/tags.css',
        ),
        'home': (
            'css/showfor.css',
            'css/wiki_syntax.css',
            'css/home.css',
        ),
        'gallery': (
            'css/to-delete.css',
            'css/gallery.css',
        ),
        'ie': (
            'css/ie.css',
            'css/ie8.css',
        ),
        'ie8': (  # IE 8 needs some specific help.
            'css/ie8.css',
        ),
        'customercare': (
            'css/customercare.css',
        ),
        'chat': (
            'css/chat.css',
        ),
        'users': (
            'css/users.css',
        ),
        'monitor': (
            'css/monitor.css',
        ),
        'mobile': (
            'global/mobile.css',
            'css/mobile.css',
            'css/wiki_syntax.css',
        ),
        'messages': (
            'css/users.autocomplete.css',
            'css/messages.css',
        ),
        'groups': (
            'css/users.autocomplete.css',
            'css/users.list.css',
            'css/groups.css',
            'css/wiki_syntax.css',
        ),
    },
    'js': {
        'common': (
            'js/i18n.js',
            'js/libs/jquery.min.js',
            'js/libs/modernizr-1.7.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.placeholder.js',
            'js/browserdetect.js',
            'js/kbox.js',
            'global/menu.js',
            'js/main.js',
            'js/format.js',
            'js/loadtest.js',
        ),
        'libs/jqueryui': (
            'js/libs/jqueryui.min.js',
        ),
        'questions': (
            'js/markup.js',
            'js/libs/jquery.ajaxupload.js',
            'js/ajaxvote.js',
            'js/aaq.js',
            'js/upload.js',
            'js/questions.js',
            'js/tags.js',
        ),
        'search': (
            'js/search.js',
        ),
        'forums': (
            'js/markup.js',
            'js/forums.js',
        ),
        'gallery': (
            'js/libs/jquery.ajaxupload.js',
            'js/gallery.js',
        ),
        'wiki': (
            'js/markup.js',
            'js/libs/django/urlify.js',
            'js/libs/django/prepopulate.js',
            'js/libs/swfobject.js',
            'js/libs/jquery.selectbox-1.2.js',
            'js/libs/jquery.autocomplete.js',
            'js/users.autocomplete.js',
            'js/screencast.js',
            'js/showfor.js',
            'js/ajaxvote.js',
            'js/wiki.js',
            'js/tags.js',
            'js/dashboards.js',
            'js/editable.js',
        ),
        'wiki.history': (
            'js/historycharts.js',
        ),
        'dashboard.helpful': (
            'js/helpfuldashcharts.js',
        ),
        'highcharts': (
            'js/libs/highcharts-2.1.4/highcharts.src.js',
        ),
        'customercare': (
            'js/libs/jquery.NobleCount.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.bullseye-1.0.min.js',
            'js/customercare.js',
            'js/users.js',
        ),
        'chat': (
            'js/chat.js',
        ),
        'users': (
            'js/users.js',
        ),
        'mobile': (
            'global/mobilefeatures.js',
            'js/i18n.js',
            'js/libs/jquery.min.js',
            'js/libs/jquery.cookie.js',
            'js/browserdetect.js',
            'js/showfor.js',
            'js/ajaxvote.js',
            'js/aaq.js',
            'js/mobile.js',
        ),
        'messages': (
            'js/libs/jquery.autocomplete.js',
            'js/users.autocomplete.js',
        ),
        'groups': (
            'js/libs/jquery.autocomplete.js',
            'js/users.autocomplete.js',
            'js/markup.js',
            'js/groups.js',
            'js/editable.js',
        ),
        'home': (
            'js/libs/jquery.selectbox-1.2.js',
            'js/showfor.js',
            'js/home.js',
        ),
        'readtracker': (
            'js/readtracker.js',
        ),
    },
}

JAVA_BIN = '/usr/bin/java'

#
# Sessions
SESSION_COOKIE_AGE = 4 * 7 * 24 * 60 * 60  # 4 weeks
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_EXISTS_COOKIE = 'sumo_session'

#
# Connection information for Sphinx search
SPHINX_HOST = '127.0.0.1'
SPHINX_PORT = 3381
SPHINXQL_PORT = 3382

SPHINX_INDEXER = '/usr/bin/indexer'
SPHINX_SEARCHD = '/usr/bin/searchd'
SPHINX_CONFIG_PATH = path('configs/sphinx/sphinx.conf')

TEST_SPHINX_PATH = path('tmp/test/sphinx')
TEST_SPHINX_PORT = 3416
TEST_SPHINXQL_PORT = 3418

SEARCH_MAX_RESULTS = 1000
SEARCH_RESULTS_PER_PAGE = 10

# Search default settings
# comma-separated tuple of included category IDs. Negative IDs are excluded.
SEARCH_DEFAULT_CATEGORIES = (10, 20,)
SEARCH_SUMMARY_LENGTH = 275

# The length for which we would like the user to cache search forms and
# results, in minutes.
SEARCH_CACHE_PERIOD = 15

# Maximum length of the filename. Forms should use this and raise
# ValidationError if the length is exceeded.
# @see http://code.djangoproject.com/ticket/9893
# Columns are 250 but this leaves 50 chars for the upload_to prefix
MAX_FILENAME_LENGTH = 200
MAX_FILEPATH_LENGTH = 250
# Default storage engine - ours does not preserve filenames
DEFAULT_FILE_STORAGE = 'upload.storage.RenameFileStorage'

# Auth and permissions related constants
LOGIN_URL = '/users/login'
LOGOUT_URL = '/users/logout'
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
REGISTER_URL = '/users/register'

# Video settings, hard coded here for now.
# TODO: figure out a way that doesn't need these values
WIKI_VIDEO_WIDTH = 640
WIKI_VIDEO_HEIGHT = 480

IMAGE_MAX_FILESIZE = 1048576  # 1 megabyte, in bytes
THUMBNAIL_SIZE = 120  # Thumbnail size, in pixels
THUMBNAIL_UPLOAD_PATH = 'uploads/images/thumbnails/'
IMAGE_UPLOAD_PATH = 'uploads/images/'
# A string listing image mime types to accept, comma separated.
# String must not contain double quotes!
IMAGE_ALLOWED_MIMETYPES = 'image/jpeg,image/png,image/gif'

# How long do we cache the question counts (in seconds)?
QUESTIONS_COUNT_TTL = 900  # 15 minutes.

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# Read-only mode setup.
READ_ONLY = False


# Turn on read-only mode in settings_local.py by putting this line
# at the VERY BOTTOM: read_only_mode(globals())
def read_only_mode(env):
    env['READ_ONLY'] = True

    # Replace the default (master) db with a slave connection.
    if not env.get('SLAVE_DATABASES'):
        raise Exception("We need at least one slave database.")
    slave = env['SLAVE_DATABASES'][0]
    env['DATABASES']['default'] = env['DATABASES'][slave]

    # No sessions without the database, so disable auth.
    env['AUTHENTICATION_BACKENDS'] = ()

    # Add in the read-only middleware before csrf middleware.
    extra = 'sumo.middleware.ReadOnlyMiddleware'
    before = 'session_csrf.CsrfMiddleware'
    m = list(env['MIDDLEWARE_CLASSES'])
    m.insert(m.index(before), extra)
    env['MIDDLEWARE_CLASSES'] = tuple(m)


# Celery
import djcelery
djcelery.setup_loader()

BROKER_HOST = 'localhost'
BROKER_PORT = 5672
BROKER_USER = 'kitsune'
BROKER_PASSWORD = 'kitsune'
BROKER_VHOST = 'kitsune'
CELERY_RESULT_BACKEND = 'amqp'
CELERY_IGNORE_RESULT = True
CELERY_ALWAYS_EAGER = True  # For tests. Set to False for use.
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERYD_LOG_LEVEL = logging.INFO
CELERYD_CONCURRENCY = 4
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True  # Explode loudly during tests.
CELERY_IMPORTS = ['django_arecibo.tasks']

# Wiki rebuild settings
WIKI_REBUILD_TOKEN = 'sumo:wiki:full-rebuild'

# Anonymous user cookie
ANONYMOUS_COOKIE_NAME = 'SUMO_ANONID'
ANONYMOUS_COOKIE_MAX_AGE = 30 * 86400  # Seconds

# Top contributors cache settings
TOP_CONTRIBUTORS_CACHE_KEY = 'sumo:TopContributors'
TOP_CONTRIBUTORS_CACHE_TIMEOUT = 60 * 60 * 12

# Do not change this without also deleting all wiki documents:
WIKI_DEFAULT_LANGUAGE = LANGUAGE_CODE

# Gallery settings
GALLERY_DEFAULT_LANGUAGE = WIKI_DEFAULT_LANGUAGE
GALLERY_IMAGE_PATH = 'uploads/gallery/images/'
GALLERY_IMAGE_THUMBNAIL_PATH = 'uploads/gallery/images/thumbnails/'
GALLERY_VIDEO_PATH = 'uploads/gallery/videos/'
GALLERY_VIDEO_URL = None
GALLERY_VIDEO_THUMBNAIL_PATH = 'uploads/gallery/videos/thumbnails/'
GALLERY_VIDEO_THUMBNAIL_PROGRESS_URL = MEDIA_URL + 'img/video-thumb.png'
THUMBNAIL_PROGRESS_WIDTH = 32  # width of the above image
THUMBNAIL_PROGRESS_HEIGHT = 32  # height of the above image
VIDEO_MAX_FILESIZE = 16777216  # 16 megabytes, in bytes

# Customer Care settings
CC_MAX_TWEETS = 500  # Max. no. of tweets in DB
CC_TWEETS_PERPAGE = 100  # How many tweets to collect in one go. Max: 100.
CC_SHOW_REPLIES = True  # Show replies to tweets?
CC_ALLOW_REMOVE = True  # Allow users to hide tweets?

CC_TWEET_ACTIVITY_URL = 'https://metrics.mozilla.com/stats/twitter/armyOfAwesomeKillRate.json'  # Tweet activity stats
CC_TOP_CONTRIB_URL = 'https://metrics.mozilla.com/stats/twitter/armyOfAwesomeTopSoldiers.json'  # Top contributor stats
CC_TWEET_ACTIVITY_CACHE_KEY = 'sumo-cc-tweet-stats'
CC_TOP_CONTRIB_CACHE_KEY = 'sumo-cc-top-contrib-stats'
CC_STATS_CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours
CC_STATS_WARNING = 30 * 60 * 60  # Warn if JSON data is older than 30 hours
CC_IGNORE_USERS = ['fx4status']  # User names whose tweets to ignore.

TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''


TIDINGS_FROM_ADDRESS = 'notifications@support.mozilla.com'
# Anonymous watches must be confirmed.
TIDINGS_CONFIRM_ANONYMOUS_WATCHES = True
TIDINGS_MODEL_BASE = 'sumo.models.ModelBase'
TIDINGS_REVERSE = 'sumo.urlresolvers.reverse'


# URL of the chat server.
CHAT_SERVER = 'https://chat-support.mozilla.com:9091'
CHAT_CACHE_KEY = 'sumo-chat-queue-status'

WEBTRENDS_WIKI_REPORT_URL = 'https://example.com/see_production.rst'
WEBTRENDS_USER = r'someaccount\someusername'
WEBTRENDS_PASSWORD = 'password'
WEBTRENDS_EPOCH = date(2010, 8, 1)  # When WebTrends started gathering stats on
                                    # the KB
WEBTRENDS_REALM = 'Webtrends Basic Authentication'

MOBILE_COOKIE = 'msumo'

# Directory of JavaScript test files for django_qunit to run
QUNIT_TEST_DIRECTORY = os.path.join(MEDIA_ROOT, 'js', 'tests')

# Key to access /services/version. Set to None to disallow.
VERSION_CHECK_TOKEN = None

REDIS_BACKENDS = {
    #'default': 'redis://localhost:6379?socket_timeout=0.5&db=0',
    #'karma': 'redis://localhost:6381?socket_timeout=0.5&db=0',
    #'helpfulvotes': 'redis://localhost:6379?socket_timeout=0.5&db=1',
}

# Redis backends used for testing.
REDIS_TEST_BACKENDS = {
    #'default': 'redis://localhost:6383?socket_timeout=0.5&db=0',
    #'karma': 'redis://localhost:6383?socket_timeout=0.5&db=1',
    #'helpfulvotes': 'redis://localhost:6379?socket_timeout=0.5&db=1',
}

# Set this to enable Arecibo (http://www.areciboapp.com/) error reporting:
ARECIBO_SERVER_URL = ''

HELPFULVOTES_UNHELPFUL_KEY = 'helpfulvotes_topunhelpful'
