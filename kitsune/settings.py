# Django settings for kitsune project.
from datetime import date
import logging
import os
import platform

from bundles import MINIFY_BUNDLES
from sumo_locales import LOCALES

DEBUG = True
TEMPLATE_DEBUG = DEBUG
STAGE = False

LOG_LEVEL = logging.INFO
SYSLOG_TAG = 'http_sumo_app'

# Repository directory.
ROOT = os.path.dirname(os.path.dirname(__file__))

# Django project directory.
PROJECT_ROOT = os.path.dirname(__file__)

PROJECT_MODULE = 'kitsune'

# path bases things off of ROOT
path = lambda *a: os.path.abspath(os.path.join(ROOT, *a))

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3'
        # or 'oracle'.
        'ENGINE': 'django.db.backends.mysql',
        # Or path to database file if sqlite3.
        'NAME': 'kitsune',
        # Not used with sqlite3.
        'USER': '',
        # Not used with sqlite3.
        'PASSWORD': '',
        # Set to empty string for localhost. Not used with sqlite3.
        'HOST': '',
        # Set to empty string for default. Not used with sqlite3.
        'PORT': '',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
    }
}

DATABASE_ROUTERS = ('multidb.PinningMasterSlaveRouter',)

# Put the aliases for your slave databases in this list
SLAVE_DATABASES = []

# Cache Settings
# CACHES = {
#     'default': {
#         'BACKEND': 'caching.backends.memcached.CacheClass',
#         'LOCATION': ['localhost:11211'],
#         'PREFIX': 'sumo:',
#     },
# }

# Setting this to the Waffle version.
WAFFLE_CACHE_PREFIX = 'w0.7.7a:'

# Addresses email comes from
DEFAULT_FROM_EMAIL = 'notifications@support.mozilla.org'
SERVER_EMAIL = 'server-error@support.mozilla.org'
EMAIL_SUBJECT_PREFIX = '[support] '

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
# Note: We periodically add locales to this list and it is easier to
# review with changes with one locale per line.
SUMO_LANGUAGES = (
    'ach',
    'ak',
    'ar',
    'as',
    'ast',
    'az',
    'be',
    'bg',
    'bn-BD',
    'bn-IN',
    'bs',
    'ca',
    'cs',
    'da',
    'de',
    'el',
    'en-US',
    'eo',
    'es',
    'et',
    'eu',
    'fa',
    'ff',
    'fi',
    'fr',
    'fur',
    'fy-NL',
    'ga-IE',
    'gd',
    'gl',
    'gu-IN',
    'he',
    'hi-IN',
    'hr',
    'hu',
    'hy-AM',
    'id',
    'ilo',
    'is',
    'it',
    'ja',
    'kk',
    'km',
    'kn',
    'ko',
    'lg',
    'lt',
    'mai',
    'mk',
    'ml',
    'mn',
    'mr',
    'ms',
    'my',
    'nb-NO',
    'ne-NP',
    'nl',
    'no',
    'nso',
    'pa-IN',
    'pl',
    'pt-BR',
    'pt-PT',
    'rm',
    'ro',
    'ru',
    'rw',
    'sah',
    'si',
    'sk',
    'sl',
    'son',
    'sq',
    'sr-Cyrl',
    'sr-Latn',
    'sv',
    'sw',
    'ta-LK',
    'ta',
    'te',
    'th',
    'tr',
    'uk',
    'vi',
    'xx',  # This is a test locale
    'zh-CN',
    'zh-TW',
    'zu',
)

# A list of locales for which AAQ is available.
AAQ_LANGUAGES = (
    'en-US',
    'pt-BR',
    'xx',  # This is a test locale
)

# Languages that should show up in language switcher.
LANGUAGE_CHOICES = tuple(
    [(lang, LOCALES[lang].native) for lang in SUMO_LANGUAGES
     if lang != 'xx'])
LANGUAGES = dict([(i.lower(), LOCALES[i].native) for i in SUMO_LANGUAGES])

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in SUMO_LANGUAGES])

# Locales that are known but unsupported. Keys are the locale, values
# are an optional fallback locale, or None, to use the LANGUAGE_CODE.
NON_SUPPORTED_LOCALES = {
    'af': None,
    'an': 'es',
    'br': 'fr',
    'csb': 'pl',
    'lij': 'it',
    'nb-NO': 'no',
    'nn-NO': 'no',
    'oc': 'fr',
    'sr': 'sr-CYRL',  # Override the tendency to go sr->sr-LATN.
    'sv-SE': 'sv',
}

TEXT_DOMAIN = 'messages'

SITE_ID = 1


# If you set this to False, Django will make some optimizations so as
# not to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

DB_LOCALIZE = {
    'karma': {
        'Title': {
            'attrs': ['name'],
            'comments': ['This is a karma title.'],
        }
    },
    'products': {
        'Product': {
            'attrs': ['title', 'description'],
        }
    },
    'topics': {
        'Topic': {
            'attrs': ['title', 'description'],
        }
    },
}

# locale is in the kitsune git repo project directory, so that's
# up one directory from the PROJECT_ROOT
LOCALE_PATHS = (
    path('locale'),
)

# Use the real robots.txt?
ENGAGE_ROBOTS = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

STATIC_ROOT = path('static')
STATIC_URL = '/static/'

# Paths that don't require a locale prefix.
SUPPORTED_NONLOCALES = ('media', 'admin', 'robots.txt', 'services', '1',
                        'postcrash', 'wafflejs', 'favicon.ico')

# Make this unique, and don't share it with anybody.
SECRET_KEY = '#%tc(zja8j01!r#h_y)=hy!^k)9az74k+-ib&ij&+**s3-e^_z'

# List of callables that know how to import templates from various
# sources.
TEMPLATE_LOADERS = (
    'jingo.Loader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

# Because Jinja2 is the default template loader, add any non-Jinja templated
# apps here:
JINGO_EXCLUDE_APPS = [
    'admin',
    'adminplus',
    'authority',
    'kadmin',
    'waffle',
]

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'session_csrf.context_processor',

    'django.contrib.messages.context_processors.messages',

    'sumo.context_processors.global_settings',
    'sumo.context_processors.for_data',
    'sumo.context_processors.i18n',
    'jingo_minify.helpers.build_ids',
    'messages.context_processors.unread_message_count',
)

MIDDLEWARE_CLASSES = (
    'multidb.middleware.PinningRouterMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'commonware.request.middleware.SetRemoteAddrFromForwardedFor',

    # This gives us atomic success or failure on multi-row writes. It
    # does not give us a consistent per-transaction snapshot for
    # reads; that would need the serializable isolation level (which
    # InnoDB does support) and code to retry transactions that roll
    # back due to serialization failures. It's a possibility for the
    # future. Keep in mind that memcache defeats snapshotted reads
    # where we don't explicitly use the "uncached" manager.
    'django.middleware.transaction.TransactionMiddleware',

    # LocaleURLMiddleware requires access to request.user. These two must be
    # loaded before the LocaleURLMiddleware
    'commonware.middleware.NoVarySessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # LocaleURLMiddleware must be before any middleware that uses
    # sumo.urlresolvers.reverse() to add locale prefixes to URLs:
    'sumo.middleware.LocaleURLMiddleware',

    # Mobile detection should happen in Zeus.
    'mobility.middleware.DetectMobileMiddleware',
    'mobility.middleware.XMobileMiddleware',
    'sumo.middleware.MobileSwitchMiddleware',

    'sumo.middleware.Forbidden403Middleware',
    'django.middleware.common.CommonMiddleware',
    'sumo.middleware.RemoveSlashMiddleware',
    'inproduct.middleware.EuBuildMiddleware',
    'sumo.middleware.NoCacheHttpsMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'sumo.anonymous.AnonymousIdentityMiddleware',
    'session_csrf.CsrfMiddleware',
    'twitter.middleware.SessionMiddleware',
    'sumo.middleware.PlusToSpaceMiddleware',
    'commonware.middleware.ScrubRequestOnException',
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'commonware.middleware.ContentTypeOptionsHeader',
    'commonware.middleware.StrictTransportMiddleware',
    'commonware.middleware.XSSProtectionHeader',
    'commonware.middleware.RobotsTagHeader',
)

# Auth
AUTHENTICATION_BACKENDS = ('django.contrib.auth.backends.ModelBackend',)
AUTH_PROFILE_MODULE = 'users.Profile'
USER_AVATAR_PATH = 'uploads/avatars/'
DEFAULT_AVATAR = MEDIA_URL + 'img/avatar.png'
AVATAR_SIZE = 48  # in pixels
MAX_AVATAR_FILE_SIZE = 131072  # 100k, in bytes
GROUP_AVATAR_PATH = 'uploads/groupavatars/'

ACCOUNT_ACTIVATION_DAYS = 30

PASSWORD_HASHERS = (
    'users.hashers.SHA256PasswordHasher',
)

USERNAME_BLACKLIST = path('kitsune', 'configs', 'username-blacklist.txt')

ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path('kitsune', 'templates'),
)

# TODO: Figure out why changing the order of apps (for example, moving
# taggit higher in the list) breaks tests.
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'users',
    'tower',
    'jingo_minify',
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
    'inproduct',
    'postcrash',
    'landings',
    'announcements',
    'messages',
    'commonware.response.cookies',
    'groups',
    'karma',
    'tags',
    'kpi',
    'products',
    'topics',

    # App for Sentry:
    'raven.contrib.django',

    # Extra apps for testing.
    'django_nose',
    'test_utils',

    # Extra app for python migrations.
    'django_extensions',

    # App for sample data
    'eadred',
)

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'


def JINJA_CONFIG():
    import jinja2
    from django.conf import settings
    from caching.base import cache
    config = {'extensions': ['tower.template.i18n', 'caching.ext.cache',
                             'jinja2.ext.autoescape', 'jinja2.ext.with_'],
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

# Tells the extract script what files to look for l10n in and what
# function handles the extraction.  The Tower library expects this.
tower_tmpl = 'tower.management.commands.extract.extract_tower_template'
tower_python = 'tower.management.commands.extract.extract_tower_python'
DOMAIN_METHODS = {
    'messages': [
        ('apps/forums/**.py', 'ignore'),
        ('apps/forums/**.html', 'ignore'),
        ('apps/**/tests/**.py', 'ignore'),
        ('apps/**/management/**.py', 'ignore'),

        ('apps/**.py', tower_python),
        ('apps/**/templates/**.html', tower_tmpl),
        ('templates/**.html', tower_tmpl),
    ],
    'lhtml': [
        ('apps/forums/**.lhtml', 'ignore'),
        ('apps/questions/**.lhtml', 'ignore'),

        ('**/templates/**.lhtml', tower_tmpl)
    ],
    'ltxt': [
        ('**/templates/**.ltxt', tower_tmpl),
    ],
    'javascript': [
        # We can't say **.js because that would dive into any libraries.
        ('media/js/*-all.js', 'ignore'),
        ('media/js/*-min.js', 'ignore'),
        ('media/js/*.js', 'javascript'),
    ],
}

# These domains will not be merged into messages.pot and will use
# separate PO files. See the following URL for an example of how to
# set these domains in DOMAIN_METHODS.
# http://github.com/jbalogh/zamboni/blob/d4c64239c24aa2f1e91276909823d1d1b290f0ee/settings.py#L254 # nopep8
STANDALONE_DOMAINS = [
    TEXT_DOMAIN,
    'javascript',
]

# If you have trouble extracting strings with Tower, try setting this
# to True
TOWER_ADD_HEADERS = True

JAVA_BIN = '/usr/bin/java'

LESS_BIN = 'lessc'

#
# Sessions
SESSION_COOKIE_AGE = 4 * 7 * 24 * 60 * 60  # 4 weeks
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_EXISTS_COOKIE = 'sumo_session'

#
# Connection information for Elastic
ES_URLS = ['http://127.0.0.1:9200']
# Indexes for reading
ES_INDEXES = {'default': 'sumo-20130506'}
# Indexes for indexing--set this to ES_INDEXES if you want to read to
# and write to the same index.
ES_WRITE_INDEXES = ES_INDEXES
# This is prepended to index names to get the final read/write index
# names used by kitsune. This is so that you can have multiple
# environments pointed at the same ElasticSearch cluster and not have
# them bump into one another.
ES_INDEX_PREFIX = 'sumo'
# Keep indexes up to date as objects are made/deleted.
ES_LIVE_INDEXING = False
# Timeout for querying requests
ES_TIMEOUT = 5

SEARCH_MAX_RESULTS = 1000
SEARCH_RESULTS_PER_PAGE = 10

# Search default settings
SEARCH_DEFAULT_CATEGORIES = (10, 20,)
SEARCH_DEFAULT_MAX_QUESTION_AGE = 180 * 24 * 60 * 60  # seconds

# IA default settings
IA_DEFAULT_CATEGORIES = (10, 20,)

# The length for which we would like the user to cache search forms
# and results, in minutes.
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

# Topics
TOPIC_IMAGE_PATH = 'uploads/topics/'

# Products
PRODUCT_IMAGE_PATH = 'uploads/products/'

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
    env['AUTHENTICATION_BACKENDS'] = ('sumo.readonlyauth.ReadOnlyBackend',)

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
VIDEO_MAX_FILESIZE = 52428800  # 50 megabytes, in bytes

# Customer Care settings
CC_MAX_TWEETS = 500  # Max. no. of tweets in DB
CC_TWEETS_PERPAGE = 100  # How many tweets to collect in one go. Max: 100.
CC_SHOW_REPLIES = True  # Show replies to tweets?
CC_ALLOW_REMOVE = True  # Allow users to hide tweets?

CC_TOP_CONTRIB_CACHE_KEY = 'sumo-cc-top-contrib-stats'
CC_TOP_CONTRIB_SORT = '1w'
CC_TOP_CONTRIB_LIMIT = 10

CC_STATS_CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours
CC_STATS_WARNING = 30 * 60 * 60  # Warn if JSON data is older than 30 hours
CC_IGNORE_USERS = ['fx4status']  # User names whose tweets to ignore.
CC_REPLIES_GOAL = 175  # Goal # of replies in 24 hours.
CC_TWEETS_DAYS = 7  # Limit tweets to those from the last 7 days.
CC_BANNED_USERS = ['lucasbytegenius']  # Twitter handles banned from AoA

TWITTER_COOKIE_SECURE = True
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
TWITTER_ACCESS_TOKEN = ''
TWITTER_ACCESS_TOKEN_SECRET = ''

TIDINGS_FROM_ADDRESS = 'notifications@support.mozilla.org'
# Anonymous watches must be confirmed.
TIDINGS_CONFIRM_ANONYMOUS_WATCHES = True
TIDINGS_MODEL_BASE = 'sumo.models.ModelBase'
TIDINGS_REVERSE = 'sumo.urlresolvers.reverse'


# Google Analytics settings.
GA_KEY = 'longkey'  # Google API client key
GA_ACCOUNT = 'something@developer.gserviceaccount.com'  # Google API Service Account email address
GA_PROFILE_ID = '12345678'  # Google Analytics profile id for SUMO prod
GA_START_DATE = date(2012, 11, 10)

MOBILE_COOKIE = 'msumo'
MOBILE_USER_AGENTS = 'android|fennec|mobile|iphone|opera (?:mini|mobi)'

# Directory of JavaScript test files for django_qunit to run
QUNIT_TEST_DIRECTORY = os.path.join(MEDIA_ROOT, 'js', 'tests')

# Key to access /services/version. Set to None to disallow.
VERSION_CHECK_TOKEN = None

REDIS_BACKENDS = {
    #'default': 'redis://localhost:6379?socket_timeout=0.5&db=0',
    #'karma': 'redis://localhost:6381?socket_timeout=0.5&db=0',
    #'helpfulvotes': 'redis://localhost:6379?socket_timeout=0.5&db=1',
}

HELPFULVOTES_UNHELPFUL_KEY = 'helpfulvotes_topunhelpful'

LAST_SEARCH_COOKIE = 'last_search'

OPTIPNG_PATH = None

# Zendesk info. Fill in the prefix, email and password in settings_local.py.
ZENDESK_URL = 'https://appsmarket.zendesk.com'
ZENDESK_SUBJECT_PREFIX = '[TEST] '  # Set to '' in prod
ZENDESK_USER_EMAIL = ''
ZENDESK_USER_PASSWORD = ''

# Tasty Pie
API_LIMIT_PER_PAGE = 0

# Change the default for XFrameOptionsMiddleware.
X_FRAME_OPTIONS = 'DENY'

# Where to find the about:support troubleshooting addon.
# This is a link to the latest version, whatever that may be.
TROUBLESHOOTER_ADDON_URL = 'https://addons.mozilla.org/firefox/downloads/latest/426841/addon-426841-latest.xpi'
