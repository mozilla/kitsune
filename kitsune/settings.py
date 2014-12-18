# -*- coding: utf-8 -*-
"""Django settings for kitsune project."""

import logging
import os
import platform
import re
from datetime import date

from bundles import MINIFY_BUNDLES
from kitsune.lib.sumo_locales import LOCALES

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
#         'BACKEND': 'caching.backends.memcached.MemcachedCache',
#         'LOCATION': ['localhost:11211'],
#         'PREFIX': 'sumo:',
#     },
# }

# Setting this to the Waffle version.
WAFFLE_CACHE_PREFIX = 'w0.7.7a:'

# Addresses email comes from
DEFAULT_FROM_EMAIL = 'notifications@support.mozilla.org'
DEFAULT_REPLY_TO_EMAIL = 'no-reply@mozilla.org'
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
    'ar',
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
    'es',
    'et',
    'eu',
    'fa',
    'fi',
    'fr',
    'fy-NL',
    'gu-IN',
    'he',
    'hi-IN',
    'hr',
    'hu',
    'id',
    'it',
    'ja',
    'km',
    'ko',
    'lt',
    'ne-NP',
    'nl',
    'no',
    'pl',
    'pt-BR',
    'pt-PT',
    'ro',
    'ru',
    'si',
    'sk',
    'sl',
    'sq',
    'sr-Cyrl',
    'sv',
    'ta',
    'ta-LK',
    'te',
    'th',
    'tr',
    'uk',
    'ur',
    'vi',
    'xx',  # This is a test locale
    'zh-CN',
    'zh-TW',
)

# These languages won't show a warning about FxOS when contributors try
# to add content.
FXOS_LANGUAGES = [
    'bn-BD',
    'bn-IN',
    'cs',
    'de',
    'el',
    'en-US',
    'es',
    'fr',
    'hi-IN',
    'hr',
    'hu',
    'it',
    'nl',
    'pl',
    'pt-BR',
    'pt-PT',
    'ro',
    'ru',
    'sr',
    'ta',
    'sr-Cyrl',
    'tr',
]

# These languages will get a wiki page instead of the product and topic pages.
SIMPLE_WIKI_LANGUAGES = [
    'et',
]

# Languages that should show up in language switcher.
LANGUAGE_CHOICES = tuple(
    [(lang, LOCALES[lang].native) for lang in SUMO_LANGUAGES
     if lang != 'xx'])
LANGUAGE_CHOICES_ENGLISH = tuple(
    [(lang, LOCALES[lang].english) for lang in SUMO_LANGUAGES
     if lang != 'xx'])
LANGUAGES_DICT = dict([(i.lower(), LOCALES[i].native) for i in SUMO_LANGUAGES])
LANGUAGES = LANGUAGES_DICT.items()

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in SUMO_LANGUAGES])

# Locales that are known but unsupported. Keys are the locale, values
# are an optional fallback locale, or None, to use the LANGUAGE_CODE.
NON_SUPPORTED_LOCALES = {
    'ach': None,
    'af': None,
    'ak': None,
    'an': 'es',
    'as': None,
    'ast': 'es',
    'az': None,
    'be': 'ru',
    'bn': 'bn-BD',
    'br': 'fr',
    'csb': 'pl',
    'eo': None,
    'ff': None,
    'fur': 'it',
    'ga-IE': None,
    'gd': None,
    'gl': 'es',
    'hsb': 'de',
    'hy-AM': None,
    'ilo': None,
    'is': None,
    'kk': None,
    'kn': None,
    'lg': None,
    'lij': 'it',
    'mai': None,
    'mk': None,
    'ml': None,
    'mn': None,
    'mr': None,
    'ms': None,
    'my': None,
    'nb-NO': 'no',
    'nn-NO': 'no',
    'nso': None,
    'oc': 'fr',
    'pa-IN': None,
    'rm': None,
    'rw': None,
    'sah': None,
    'son': None,
    'sv-SE': 'sv',
    'sw': None,
    'xh': None,
    'zu': None,
}

ES_LOCALE_ANALYZERS = {
    'ar': 'arabic',
    'bg': 'bulgarian',
    'ca': 'snowball-catalan',
    'cs': 'czech',
    'da': 'snowball-danish',
    'de': 'snowball-german',
    'en-US': 'snowball-english',
    'es': 'snowball-spanish',
    'eu': 'snowball-basque',
    'fa': 'persian',
    'fi': 'snowball-finnish',
    'fr': 'snowball-french',
    'hi-IN': 'hindi',
    'hu': 'snowball-hungarian',
    'id': 'indonesian',
    'it': 'snowball-italian',
    'ja': 'cjk',
    'nl': 'snowball-dutch',
    'no': 'snowball-norwegian',
    'pl': 'polish',
    'pt-BR': 'snowball-portuguese',
    'pt-PT': 'snowball-portuguese',
    'ro': 'snowball-romanian',
    'ru': 'snowball-russian',
    'sv': 'snowball-swedish',
    'th': 'thai',
    'tr': 'snowball-turkish',
    'zh-CN': 'chinese',
    'zh-TW': 'chinese',
}

ES_PLUGIN_ANALYZERS = [
    'polish'
]

ES_USE_PLUGINS = False

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
        },
        'Topic':  {
            'attrs': ['title', 'description'],
        },
    },
    'badger': {
        'Badge': {
            'attrs': ['title', 'description'],
        },
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
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'kitsune.sumo.static_finders.WTFinder')

# Paths that don't require a locale prefix.
SUPPORTED_NONLOCALES = (
    '1',
    'admin',
    'api',
    'favicon.ico',
    'media',
    'postcrash',
    'robots.txt',
    'services',
    'wafflejs',
    'geoip-suggestion',
)

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
    'rest_framework',
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

    'kitsune.sumo.context_processors.global_settings',
    'kitsune.sumo.context_processors.i18n',
    'kitsune.sumo.context_processors.geoip_cache_detector',
    'kitsune.sumo.context_processors.aaq_languages',
    'jingo_minify.helpers.build_ids',
    'kitsune.messages.context_processors.unread_message_count',
)

MIDDLEWARE_CLASSES = (
    'multidb.middleware.PinningRouterMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'commonware.request.middleware.SetRemoteAddrFromForwardedFor',

    # LocaleURLMiddleware requires access to request.user. These two must be
    # loaded before the LocaleURLMiddleware
    'commonware.middleware.NoVarySessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'kitsune.users.middleware.LogoutDeactivatedUsersMiddleware',

    # This should come before TokenLoginMiddleware, because
    # TokenLoginMiddleware uses this to tell users they have been
    # automatically logged. It also has to come after
    # NoVarySessionMiddleware.
    'django.contrib.messages.middleware.MessageMiddleware',

    # This middleware should come after AuthenticationMiddleware.
    'kitsune.users.middleware.TokenLoginMiddleware',

    # LocaleURLMiddleware must be before any middleware that uses
    # sumo.urlresolvers.reverse() to add locale prefixes to URLs:
    'kitsune.sumo.middleware.LocaleURLMiddleware',

    # Mobile detection should happen in Zeus.
    'kitsune.sumo.middleware.DetectMobileMiddleware',
    'mobility.middleware.XMobileMiddleware',
    'kitsune.sumo.middleware.MobileSwitchMiddleware',

    'kitsune.sumo.middleware.Forbidden403Middleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'kitsune.sumo.middleware.RemoveSlashMiddleware',
    'kitsune.inproduct.middleware.EuBuildMiddleware',
    'kitsune.sumo.middleware.NoCacheHttpsMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'kitsune.sumo.anonymous.AnonymousIdentityMiddleware',
    'session_csrf.CsrfMiddleware',
    'kitsune.twitter.middleware.SessionMiddleware',
    'kitsune.sumo.middleware.PlusToSpaceMiddleware',
    'commonware.middleware.ScrubRequestOnException',
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'commonware.middleware.ContentTypeOptionsHeader',
    'commonware.middleware.StrictTransportMiddleware',
    'commonware.middleware.XSSProtectionHeader',
    'commonware.middleware.RobotsTagHeader',
    # 'axes.middleware.FailedLoginMiddleware'
)

# Auth
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'kitsune.users.auth.TokenLoginBackend',
)
AUTH_PROFILE_MODULE = 'users.Profile'
USER_AVATAR_PATH = 'uploads/avatars/'
DEFAULT_AVATAR = 'img/avatar.png'
AVATAR_SIZE = 48  # in pixels
MAX_AVATAR_FILE_SIZE = 131072  # 100k, in bytes
GROUP_AVATAR_PATH = 'uploads/groupavatars/'

ACCOUNT_ACTIVATION_DAYS = 30

PASSWORD_HASHERS = (
    'kitsune.users.hashers.SHA256PasswordHasher',
)

USERNAME_BLACKLIST = path('kitsune', 'configs', 'username-blacklist.txt')

ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates"
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.

    # Check templates in the sumo apps first. There are overrides for the admin
    # templates.
    path('kitsune', 'sumo', 'templates'),
)

# TODO: Figure out why changing the order of apps (for example, moving
# taggit higher in the list) breaks tests.
INSTALLED_APPS = (
    # south needs to come early so tests don't fail
    'south',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'corsheaders',
    'kitsune.users',
    'dennis.django_dennis',
    'tower',
    'jingo_minify',
    'authority',
    'timezones',
    'waffle',
    'kitsune.access',
    'kitsune.sumo',
    'kitsune.search',
    'kitsune.forums',
    'djcelery',
    'badger',
    'cronjobs',
    'tidings',
    'rest_framework.authtoken',
    'kitsune.questions',
    'adminplus',
    'kitsune.kadmin',
    'kitsune.kbadge',
    'taggit',
    'kitsune.flagit',
    'kitsune.upload',
    'product_details',
    'kitsune.wiki',
    'kitsune.kbforums',
    'kitsune.dashboards',
    'kitsune.gallery',
    'kitsune.customercare',
    'kitsune.twitter',
    'kitsune.inproduct',
    'kitsune.postcrash',
    'kitsune.landings',
    'kitsune.announcements',
    'kitsune.community',
    'kitsune.messages',
    'commonware.response.cookies',
    'kitsune.groups',
    'kitsune.karma',
    'kitsune.tags',
    'kitsune.kpi',
    'kitsune.products',
    'kitsune.notifications',
    'rest_framework',
    'statici18n',
    # 'axes',

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

TEST_RUNNER = 'kitsune.sumo.tests.TestSuiteRunner'


def JINJA_CONFIG():
    from django.conf import settings
    config = {'extensions': ['tower.template.i18n', 'caching.ext.cache',
                             'jinja2.ext.autoescape', 'jinja2.ext.with_',
                             'jinja2.ext.do'],
              'finalize': lambda x: x if x is not None else ''}

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
        ('kitsune/forums/**.py', 'ignore'),
        ('kitsune/forums/**.html', 'ignore'),
        ('kitsune/**/tests/**.py', 'ignore'),
        ('kitsune/**/management/**.py', 'ignore'),

        ('kitsune/**.py', tower_python),
        ('kitsune/**/templates/**.html', tower_tmpl),
        ('vendor/src/django-tidings/**/templates/**.html', tower_tmpl),
        ('vendor/src/django-badger/badger/*.py', tower_python),
        ('vendor/src/django-badger/badger/templatetags/*.py', tower_python),
    ],
    'lhtml': [
        ('kitsune/forums/**.lhtml', 'ignore'),

        ('**/templates/**.lhtml', tower_tmpl)
    ],
    'ltxt': [
        ('**/templates/**.ltxt', tower_tmpl),
    ],
    'javascript': [
        # We can't say **.js because that would dive into any libraries.
        ('kitsune/**/static/js/*-all.js', 'ignore'),
        ('kitsune/**/static/js/*-min.js', 'ignore'),

        ('kitsune/**/static/js/*.js', 'javascript'),
    ],
}

# These domains will not be merged into messages.pot and will use
# separate PO files. See the following URL for an example of how to
# set these domains in DOMAIN_METHODS.
# http://github.com/jbalogh/zamboni/blob/d4c64239c24aa2f1e91276909823d1d1b290f0ee/settings.py#L254 # nopep8
STANDALONE_DOMAINS = [
    TEXT_DOMAIN,
    'javascript',
    'yaocho',
]

STATICI18N_DOMAIN = 'javascript'
STATICI18N_PACKAGES = ['kitsune.sumo']

# If you have trouble extracting strings with Tower, try setting this
# to True
TOWER_ADD_HEADERS = True

LESS_BIN = 'lessc'
UGLIFY_BIN = 'uglifyjs'
CLEANCSS_BIN = 'cleancss'

NUNJUCKS_PRECOMPILE_BIN = 'nunjucks-precompile'

#
# Sessions
SESSION_COOKIE_AGE = 4 * 7 * 24 * 60 * 60  # 4 weeks
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_EXISTS_COOKIE = 'sumo_session'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

#
# Connection information for Elastic
ES_URLS = ['http://127.0.0.1:9200']
# Indexes for reading
ES_INDEXES = {
    'default': 'sumo-20130913',
    'non-critical': 'sumo-non-critical',
    'metrics': 'sumo-metrics',
}
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
DEFAULT_FILE_STORAGE = 'kitsune.upload.storage.RenameFileStorage'

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
    env['AUTHENTICATION_BACKENDS'] = ('kitsune.sumo.readonlyauth.ReadOnlyBackend',)

    # Add in the read-only middleware before csrf middleware.
    extra = 'kitsune.sumo.middleware.ReadOnlyMiddleware'
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
CELERYD_HIJACK_ROOT_LOGGER = False

# Wiki rebuild settings
WIKI_REBUILD_TOKEN = 'sumo:wiki:full-rebuild'

# Anonymous user cookie
ANONYMOUS_COOKIE_NAME = 'SUMO_ANONID'
ANONYMOUS_COOKIE_MAX_AGE = 30 * 86400  # Seconds

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
CC_REPLIES_GOAL = 175  # Goal # of replies in 24 hours.
CC_TWEETS_DAYS = 7  # Limit tweets to those from the last 7 days.

# If any of these words show up in a tweet, it probably isn't
# actionable, so don't add it to the AoA.
CC_WORD_BLACKLIST = [
    '#UninstallFirefox',
]

BITLY_API_URL = 'http://api.bitly.com/v3/shorten?callback=?'
BITLY_LOGIN = None
BITLY_API_KEY = None

TWITTER_COOKIE_SECURE = True
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
TWITTER_ACCESS_TOKEN = ''
TWITTER_ACCESS_TOKEN_SECRET = ''

TIDINGS_FROM_ADDRESS = 'notifications@support.mozilla.org'
# Anonymous watches must be confirmed.
TIDINGS_CONFIRM_ANONYMOUS_WATCHES = True
TIDINGS_MODEL_BASE = 'kitsune.sumo.models.ModelBase'
TIDINGS_REVERSE = 'kitsune.sumo.urlresolvers.reverse'


# Google Analytics settings.
GA_KEY = 'longkey'  # Google API client key
GA_ACCOUNT = 'something@developer.gserviceaccount.com'  # Google API Service Account email address
GA_PROFILE_ID = '12345678'  # Google Analytics profile id for SUMO prod
GA_START_DATE = date(2012, 11, 10)

MOBILE_COOKIE = 'msumo'

# Directory of JavaScript test files for django_qunit to run
QUNIT_TEST_DIRECTORY = os.path.join('kitsune', 'sumo', 'static', 'js', 'tests')

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

# SurveyGizmo API
SURVEYGIZMO_USER = ''
SURVEYGIZMO_PASSWORD = ''

# Django Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework.filters.DjangoFilterBackend',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
}

# Django-axes settings.
AXES_LOGIN_FAILURE_LIMIT = 10
AXES_LOCK_OUT_AT_FAILURE = True
AXES_USE_USER_AGENT = False
AXES_COOLOFF_TIME = 1  # hour
AXES_BEHIND_REVERSE_PROXY = True
AXES_REVERSE_PROXY_HEADER = 'HTTP_X_CLUSTER_CLIENT_IP'

# Set this to True to wrap each HTTP request in a transaction on this database.
ATOMIC_REQUESTS = True

# CORS Setup
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = [
    r'^/api/1/gallery/.*$',
    r'^/api/1/kb/.*$',
    r'^/api/1/products/.*',
    r'^/api/1/users/get_token$',
    r'^/api/1/users/test_auth$',
    r'^/api/2/answer/.*$',
    r'^/api/2/pushnotification/.*$',
    r'^/api/2/question/.*$',
    r'^/api/2/user/.*$',
]
# Now combine all those regexes with one big "or".
CORS_URLS_REGEX = re.compile('|'.join('({0})'.format(r) for r in CORS_URLS_REGEX))
CORS_URLS_REGEX = '.*'

# XXX Fix this when Bug 1059545 is fixed
CC_IGNORE_USERS = []
