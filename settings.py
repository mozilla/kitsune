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
# Note: We periodically add locales to this list and it is easier to review
# with changes with one locale per line.
SUMO_LANGUAGES = (
    'ach',
    'ak',
    'ar',
    'as',
    'ast',
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
    'si',
    'sk',
    'sl',
    'son',
    'sq',
    'sr-CYRL',
    'sr-LATN',
    'sv',
    'ta-LK',
    'ta',
    'te',
    'th',
    'tr',
    'uk',
    'vi',
    'zh-CN',
    'zh-TW',
    'zu',
)

LANGUAGE_CHOICES = tuple([(i, LOCALES[i].native) for i in SUMO_LANGUAGES])
LANGUAGES = dict([(i.lower(), LOCALES[i].native) for i in SUMO_LANGUAGES])

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in SUMO_LANGUAGES])

# Locales that are known but unsupported. Keys are the locale, values are
# an optional fallback locale, or None, to use the LANGUAGE_CODE.
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


# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
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
    'sumo.context_processors.i18n',
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
    'commonware.response.middleware.GraphiteRequestTimingMiddleware',
    'waffle.middleware.WaffleMiddleware',
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
    'users.hashers.PasswordDisabledHasher',
)

PASSWORD_BLACKLIST = path('configs/password-blacklist.txt')
USERNAME_BLACKLIST = path('configs/username-blacklist.txt')

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
    'django.contrib.staticfiles',
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
        ('apps/forums/**.py', 'ignore'),
        ('apps/forums/**.html', 'ignore'),
        ('apps/questions/**.py', 'ignore'),
        ('apps/questions/**.html', 'ignore'),
        ('apps/chat/**.py', 'ignore'),
        ('apps/chat/**.html', 'ignore'),
        ('apps/**/tests/**.py', 'ignore'),
        ('apps/**/management/**.py', 'ignore'),
        ('apps/**.py',
            'tower.management.commands.extract.extract_tower_python'),
        ('apps/**/templates/**.html',
            'tower.management.commands.extract.extract_tower_template'),
        ('templates/**.html',
            'tower.management.commands.extract.extract_tower_template'),
    ],
    'lhtml': [
        ('apps/forums/**.lhtml', 'ignore'),
        ('apps/questions/**.lhtml', 'ignore'),
        ('**/templates/**.lhtml',
            'tower.management.commands.extract.extract_tower_template'),
    ],
    'javascript': [
        # We can't say **.js because that would dive into any libraries.
        ('media/js/*-all.js', 'ignore'),
        ('media/js/*-min.js', 'ignore'),
        ('media/js/*.js', 'javascript'),
    ],
}

# These domains will not be merged into messages.pot and will use separate PO
# files. See the following URL for an example of how to set these domains
# in DOMAIN_METHODS.
# http://github.com/jbalogh/zamboni/blob/d4c64239c24aa2f1e91276909823d1d1b290f0ee/settings.py#L254
STANDALONE_DOMAINS = [
    TEXT_DOMAIN,
    'javascript',
    ]

# If you have trouble extracting strings with Tower, try setting this
# to True
TOWER_ADD_HEADERS = True

# Bundles for JS/CSS Minification
MINIFY_BUNDLES = {
    'css': {
        'common': (
            'css/normalize.css',
            'less/main.less',
        ),
        'print': (
            'css/print.css',
        ),
        # TODO: remove dependency on jquery ui CSS and use our own
        'jqueryui/jqueryui': (
            'css/jqueryui/jqueryui.css',
        ),
        'forums': (
            'less/forums.less',
            'less/reportabuse.less',
        ),
        'questions': (
            'less/questions.less',
            'css/cannedresponses.css',
            'less/reportabuse.less',
        ),
        'mobile/questions': (
            'less/mobile/questions.less',
        ),
        'mobile/aaq': (
            'less/mobile/aaq.less',
        ),
        'search': (
            'less/search.less',
        ),
        'mobile/search': (
            'less/mobile/search.less',
        ),
        'wiki': (
            'css/users.autocomplete.css',
            'css/users.list.css',
            'less/wiki.less',
            'css/screencast.css',
        ),
        'mobile/wiki': (
            'less/mobile/wiki.less',
        ),
        'home': (
            'less/home.less',
        ),
        'gallery': (
            'less/gallery.less',
        ),
        'ie': (
            'css/ie.css',
            'css/ie8.css',
        ),
        'ie8': (  # IE 8 needs some specific help.
            'css/ie8.css',
        ),
        'customercare': (
            'less/customercare.less',
        ),
        'chat': (
            'css/chat.css',
        ),
        'users': (
            'less/users.less',
            'less/reportabuse.less',
        ),
        'mobile/users': (
            'less/mobile/users.less',
        ),
        'monitor': (
            'css/monitor.css',
        ),
        'mobile': (
            'global/mobile.css',
            'css/mobile.css',
            'css/wiki_syntax.css',
        ),
        'mobile/new': (
            'css/normalize.css',
            'less/mobile/main.less',
        ),
        'messages': (
            'css/users.autocomplete.css',
            'less/messages.less',
        ),
        'products': (
            'less/products.less',
        ),
        'mobile/products': (
            'less/mobile/products.less',
        ),
        'groups': (
            'css/users.autocomplete.css',
            'css/users.list.css',
            'css/groups.css',
            'css/wiki_syntax.css',
        ),
        'karma.dashboard': (
            'css/karma.dashboard.css',
        ),
        'kpi.dashboard': (
            'css/kpi.dashboard.css',
        ),
        'locale-switcher': (
            'less/locale-switcher.less',
        ),
        'mobile/locale-switcher': (
            'less/mobile/locales.less',
        ),
        'kbdashboards': (
            'less/kbdashboards.less',
        ),
    },
    'js': {
        'common': (
            'js/i18n.js',
            'js/libs/underscore.js',
            'js/libs/jquery-1.7.1.min.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.placeholder.js',
            'js/browserdetect.js',
            'js/kbox.js',
            'js/main.js',
            'js/format.js',
            'js/libs/modernizr-2.6.1.js',
            'js/ui.js',
            'js/analytics.js',
            'js/surveygizmo.js',
        ),
        'ie6-8': (
            'js/libs/nwmatcher-1.2.5.js',
            'js/libs/selectivizr-1.0.2.js',
        ),
        'libs/jqueryui': (
            'js/libs/jqueryui.min.js',
        ),
        'questions': (
            'js/markup.js',
            'js/libs/jquery.ajaxupload.js',
            'js/ajaxvote.js',
            'js/ajaxpreview.js',
            'js/aaq.js',
            'js/upload.js',
            'js/questions.js',
            'js/libs/jquery.tokeninput.js',
            'js/tags.filter.js',
            'js/tags.js',
            'js/reportabuse.js',
        ),
        'mobile/questions': (
            'js/mobile/questions.js',
        ),
        'search': (
            'js/search.js',
        ),
        'forums': (
            'js/markup.js',
            'js/ajaxpreview.js',
            'js/forums.js',
            'js/reportabuse.js',
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
            'js/libs/jquery.lazyload.js',
            'js/libs/jquery.selectbox-1.2.js',
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
            'js/screencast.js',
            'js/showfor.js',
            'js/ajaxvote.js',
            'js/ajaxpreview.js',
            'js/wiki.js',
            'js/tags.js',
            'js/dashboards.js',
            'js/editable.js',
        ),
        'mobile/wiki': (
            'js/libs/underscore.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.lazyload.js',
            'js/browserdetect.js',
            'js/showfor.js',
            'js/ajaxform.js',
            'js/mobile/wiki.js'
        ),
        'wiki.history': (
            'js/historycharts.js',
        ),
        'wiki.diff': (
            'js/libs/diff_match_patch_uncompressed.js',
            'js/diff.js',
        ),
        'wiki.editor': (
            'js/libs/ace/src-min/ace.js',
            'js/libs/ace.mode-sumo.js',
        ),
        'wiki.dashboard': (
            'js/libs/backbone.js',
            'js/charts.js',
            'js/wiki.dashboard.js',
            'js/helpfuldashcharts.js',
        ),
        'highcharts': (
            'js/libs/highstock.src.js',
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
            'js/reportabuse.js',
        ),
        'mobile': (
            'js/libs/underscore.js',
            'global/mobilefeatures.js',
            'js/i18n.js',
            'js/libs/jquery.min.js',
            'js/libs/jquery.cookie.js',
            'js/libs/jquery.lazyload.js',
            'js/browserdetect.js',
            'js/showfor.js',
            'js/ajaxvote.js',
            'js/aaq.js',
            'js/mobile.js',
            'js/analytics.js',
        ),
        'mobile-new': (
            'js/libs/jquery-1.8.2.min.js',
            'js/mobile/ui.js',
            'js/libs/modernizr-2.6.1.js',
            'js/analytics.js',
        ),
        'messages': (
            'js/markup.js',
            'js/libs/jquery.autoresize.js',
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
            'js/ajaxpreview.js',
            'js/messages.js',
        ),
        'groups': (
            'js/libs/jquery.tokeninput.js',
            'js/users.autocomplete.js',
            'js/markup.js',
            'js/groups.js',
            'js/editable.js',
        ),
        'home': (
            'js/libs/jquery.lazyload.js',
            'js/libs/jquery.selectbox-1.2.js',
            'js/showfor.js',
            'js/home.js',
        ),
        'readtracker': (
            'js/readtracker.js',
        ),
        'karma.dashboard': (
            'js/libs/backbone.js',
            'js/karma.dashboard.js',
        ),
        'kpi.dashboard': (
            'js/libs/backbone.js',
            'js/charts.js',
            'js/kpi.dashboard.js',
        ),
    },
}

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
ES_HOSTS = ['127.0.0.1:9200']
# Indexes for reading
ES_INDEXES = {'default': 'sumo-20120731'}
# Indexes for indexing--set this to ES_INDEXES if you want to read to
# and write to the same index.
ES_WRITE_INDEXES = ES_INDEXES
# This is prepended to index names to get the final read/write index
# names used by kitsune. This is so that you can have multiple environments
# pointed at the same ElasticSearch cluster and not have them bump into
# one another.
ES_INDEX_PREFIX = 'sumo'
# Keep indexes up to date as objects are made/deleted.
ES_LIVE_INDEXING = False
# Timeout for querying requests
ES_TIMEOUT = 5
# Timeout for indexing requests
ES_INDEXING_TIMEOUT = 30
# Seconds between updating admin progress bar:
ES_REINDEX_PROGRESS_BAR_INTERVAL = 5
ES_FLUSH_BULK_EVERY = 100
# Time to sleep after creating indexes for tests
ES_TEST_SLEEP_DURATION = 0

SEARCH_MAX_RESULTS = 1000
SEARCH_RESULTS_PER_PAGE = 20

# Search default settings
SEARCH_DEFAULT_CATEGORIES = (10, 20,)
SEARCH_DEFAULT_MAX_QUESTION_AGE = 180 * 24 * 60 * 60  # seconds

# IA default settings
IA_DEFAULT_CATEGORIES = (10, 20,)

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

CC_TWEET_ACTIVITY_URL = 'https://metrics.mozilla.com/stats/twitter/armyOfAwesomeKillRate.json'  # Tweet activity stats
CC_TOP_CONTRIB_URL = 'https://metrics.mozilla.com/stats/twitter/armyOfAwesomeTopSoldiers.json'  # Top contributor stats
CC_TWEET_ACTIVITY_CACHE_KEY = 'sumo-cc-tweet-stats'
CC_TOP_CONTRIB_CACHE_KEY = 'sumo-cc-top-contrib-stats'
CC_STATS_CACHE_TIMEOUT = 24 * 60 * 60  # 24 hours
CC_STATS_WARNING = 30 * 60 * 60  # Warn if JSON data is older than 30 hours
CC_IGNORE_USERS = ['fx4status']  # User names whose tweets to ignore.
CC_REPLIES_GOAL = 175  # Goal # of replies in 24 hours.
CC_TWEETS_DAYS = 7  # Limit tweets to those from the last 7 days.
CC_BANNED_USERS = ['lucasbytegenius']  # Twitter handles banned from AoA

TWITTER_COOKIE_SECURE = True
TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''


TIDINGS_FROM_ADDRESS = 'notifications@support.mozilla.org'
# Anonymous watches must be confirmed.
TIDINGS_CONFIRM_ANONYMOUS_WATCHES = True
TIDINGS_MODEL_BASE = 'sumo.models.ModelBase'
TIDINGS_REVERSE = 'sumo.urlresolvers.reverse'


# URL of the chat server.
CHAT_SERVER = 'https://chat-support.mozilla.com:9091'
CHAT_CACHE_KEY = 'sumo-chat-queue-status'

WEBTRENDS_PROFILE_ID = 'ABC123'  # Profile id for SUMO
WEBTRENDS_WIKI_REPORT_URL = 'https://example.com/see_production.rst'
WEBTRENDS_USER = r'someaccount\someusername'
WEBTRENDS_PASSWORD = 'password'
WEBTRENDS_EPOCH = date(2010, 8, 1)  # When WebTrends started gathering stats on
                                    # the KB

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
