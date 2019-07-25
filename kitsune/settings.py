# -*- coding: utf-8 -*-
"""Django settings for kitsune project."""

import logging
import os
import platform
import re

import dj_database_url
import django_cache_url


from datetime import date
from decouple import Csv, config

import djcelery

from bundles import PIPELINE_CSS, PIPELINE_JS
from kitsune.lib.sumo_locales import LOCALES

DEBUG = config('DEBUG', default=False, cast=bool)
DEV = config('DEV', default=False, cast=bool)
STAGE = config('STAGE', default=False, cast=bool)

# TODO
# LOG_LEVEL = config('LOG_LEVEL', default='INFO', cast=labmda x: getattr(logging, x))
LOG_LEVEL = config('LOG_LEVEL', default=logging.INFO)

SYSLOG_TAG = 'http_sumo_app'

# Repository directory.
ROOT = os.path.dirname(os.path.dirname(__file__))

# Django project directory.
PROJECT_ROOT = os.path.dirname(__file__)

PROJECT_MODULE = 'kitsune'


# path bases things off of ROOT
def path(*parts):
    return os.path.abspath(os.path.join(ROOT, *parts))


# Read-only mode setup.
READ_ONLY = config('READ_ONLY', default=False, cast=bool)
SKIP_MOBILE_DETECTION = config('SKIP_MOBILE_DETECTION', default=False, cast=bool)
ENABLE_VARY_NOCACHE_MIDDLEWARE = config('ENABLE_VARY_NOCACHE_MIDDLEWARE', default=READ_ONLY, cast=bool)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS


# DB_CONN_MAX_AGE: 'persistent' to keep open connection, or max requests before
# releasing. Default is 0 for a new connection per request.
def parse_conn_max_age(value):
    try:
        return int(value)
    except ValueError:
        assert value.lower() == 'persistent', 'Must be int or "persistent"'
        return None


DB_CONN_MAX_AGE = config('DB_CONN_MAX_AGE', default=60, cast=parse_conn_max_age)

DATABASES = {
    'default': config('DATABASE_URL', cast=dj_database_url.parse),
}

if DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    DATABASES['default']['CONN_MAX_AGE'] = DB_CONN_MAX_AGE
    DATABASES['default']['OPTIONS'] = {'init_command': 'SET storage_engine=InnoDB'}
    DATABASE_ROUTERS = ('multidb.PinningMasterSlaveRouter',)

# Add read-only databases here. The database can be the same as the `default`
# database but with a user with read permissions only.
SLAVE_DATABASES = [
]

# Cache Settings
CACHES = {
    'default': config('CACHE_URL', default='locmem://', cast=django_cache_url.parse),
    'product-details': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'product-details',
        'OPTIONS': {
            'MAX_ENTRIES': 200,  # currently 104 json files
            'CULL_FREQUENCY':  4,  # 1/4 entries deleted if max reached
        }

    },
}

CACHE_MIDDLEWARE_SECONDS = config('CACHE_MIDDLEWARE_SECONDS',
                                  default=(2 * 60 * 60) if READ_ONLY else 0,
                                  cast=int)

# Setting this to the Waffle version.
WAFFLE_CACHE_PREFIX = 'w0.11:'

# Addresses email comes from
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='notifications@support.mozilla.org')
DEFAULT_REPLY_TO_EMAIL = config('DEFAULT_REPLY_TO_EMAIL', default='no-reply@mozilla.org')
SERVER_EMAIL = config('SERVER_EMAIL', default='server-error@support.mozilla.org')

PLATFORM_NAME = platform.node()
K8S_DOMAIN = config('K8S_DOMAIN', default='')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = config('TIME_ZONE', default='US/Pacific')

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-US'

# Supported languages
# Note: We periodically add locales to this list and it is easier to
# review with changes with one locale per line.
SUMO_LANGUAGES = (
    'af',
    'ar',
    'az',
    'bg',
    'bm',
    'bn-BD',
    'bn-IN',
    'bs',
    'ca',
    'cs',
    'da',
    'de',
    'ee',
    'el',
    'en-US',
    'es',
    'et',
    'eu',
    'fa',
    'fi',
    'fr',
    'fy-NL',
    'ga-IE',
    'gl',
    'gn',
    'gu-IN',
    'ha',
    'he',
    'hi-IN',
    'hr',
    'hu',
    'dsb',
    'hsb',
    'id',
    'ig',
    'it',
    'ja',
    'ka',
    'km',
    'kn',
    'ko',
    'ln',
    'lt',
    'mg',
    'mk',
    'ml',
    'ms',
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
    'sr',
    'sw',
    'sv',
    'ta',
    'ta-LK',
    'te',
    'th',
    'tn',
    'tr',
    'uk',
    'ur',
    'vi',
    'wo',
    'xh',
    'xx',  # This is a test locale
    'yo',
    'zh-CN',
    'zh-TW',
    'zu',
)

# These languages won't show a warning about FxOS when contributors try
# to add content.
FXOS_LANGUAGES = [
    'af',
    'bm',
    'bn-BD',
    'bn-IN',
    'cs',
    'de',
    'ee',
    'el',
    'en-US',
    'es',
    'fr',
    'ha',
    'hi-IN',
    'hr',
    'hu',
    'ig',
    'it',
    'jv',
    'ln',
    'mg',
    'nl',
    'pl',
    'pt-BR',
    'pt-PT',
    'ro',
    'ru',
    'sr',
    'ta',
    'sr',
    'su',
    'sw',
    'tr',
    'wo',
    'xh',
    'yo',
    'zu',
]

# These languages will get a wiki page instead of the product and topic pages.
SIMPLE_WIKI_LANGUAGES = [
    'az',
    'et',
    'ga-IE',
    'gl',
    'kn',
    'ml',
    'tn',
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
    'ak': None,
    'an': 'es',
    'as': None,
    'ast': 'es',
    'be': 'ru',
    'bn': 'bn-BD',
    'br': 'fr',
    'cak': None,
    'csb': 'pl',
    'cy': None,
    'eo': None,
    'ff': None,
    'fur': 'it',
    'gd': None,
    'hy-AM': None,
    'ilo': None,
    'is': None,
    'kab': None,
    'kk': None,
    'lg': None,
    'lij': 'it',
    'lo': None,
    'ltg': None,
    'lv': None,
    'mai': None,
    'mn': None,
    'mr': None,
    'my': None,
    'nb-NO': 'no',
    'nn-NO': 'no',
    'nso': None,
    'oc': 'fr',
    'or': None,
    'pa-IN': None,
    'rm': None,
    'rw': None,
    'sah': None,
    'son': None,
    'sv-SE': 'sv',
    'tl': None,
    'uz': None,
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

ES_USE_PLUGINS = config('ES_USE_PLUGINS', default=True, cast=bool)

TEXT_DOMAIN = 'messages'

SITE_ID = 1

USE_ETAGS = config('USE_ETAGS', default=False, cast=bool)
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
    'kbadge': {
        'Badge': {
            'attrs': ['title', 'description'],
        },
    },
}

# locale is in the kitsune git repo project directory, so that's
# up one directory from the PROJECT_ROOT
if config('SET_LOCALE_PATHS', default=True, cast=bool):
    LOCALE_PATHS = (
        path('locale'),
    )

# Use the real robots.txt?
ENGAGE_ROBOTS = config('ENGAGE_ROBOTS', default=not DEBUG, cast=bool)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')
MEDIA_URL = config('MEDIA_URL', default='/media/')

STATIC_ROOT = path('static')
STATIC_URL = config('STATIC_URL', default='/static/')
STATICFILES_DIRS = (
    path('bower_components'),
    path('jsi18n'),  # Collect jsi18n so that it is cache-busted
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
)

STATICFILES_STORAGE = 'kitsune.sumo.storage.SumoFilesStorage'

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
    'contribute.json',
    'oidc',
    'healthz',
    'readiness',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = config('SECRET_KEY')

_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.template.context_processors.debug',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.template.context_processors.request',

    'django.contrib.messages.context_processors.messages',

    'kitsune.sumo.context_processors.global_settings',
    'kitsune.sumo.context_processors.i18n',
    'kitsune.sumo.context_processors.aaq_languages',
    'kitsune.messages.context_processors.unread_message_count',
]

TEMPLATES = [
    {
        'BACKEND': 'django_jinja.backend.Jinja2',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            # Use jinja2/ for jinja templates
            'app_dirname': 'jinja2',
            # Don't figure out which template loader to use based on
            # file extension
            'match_extension': '',
            'newstyle_gettext': True,
            'context_processors': _CONTEXT_PROCESSORS,
            'undefined': 'jinja2.Undefined',
            'extensions': [
                'puente.ext.i18n',
                'waffle.jinja.WaffleExtension',
                'jinja2.ext.autoescape',
                'jinja2.ext.with_',
                'jinja2.ext.do',
                'pipeline.jinja2.PipelineExtension',

                'django_jinja.builtins.extensions.CsrfExtension',
                'django_jinja.builtins.extensions.StaticFilesExtension',
                'django_jinja.builtins.extensions.DjangoFiltersExtension',
            ],
        }
    },
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': _CONTEXT_PROCESSORS,
        }
    },
]


MIDDLEWARE_CLASSES = (
    'kitsune.sumo.middleware.HostnameMiddleware',
    'allow_cidr.middleware.AllowCIDRMiddleware',
    'kitsune.sumo.middleware.FilterByUserAgentMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'multidb.middleware.PinningRouterMiddleware',
    'django_statsd.middleware.GraphiteMiddleware',
    'commonware.request.middleware.SetRemoteAddrFromForwardedFor',
    'kitsune.sumo.middleware.EnforceHostIPMiddleware',

    # VaryNoCacheMiddleware must be above LocaleURLMiddleware
    # so that it can see the response has a vary on accept-language
    'kitsune.sumo.middleware.VaryNoCacheMiddleware',

    # LocaleURLMiddleware requires access to request.user. These two must be
    # loaded before the LocaleURLMiddleware
    'commonware.middleware.NoVarySessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',

    # This should come before TokenLoginMiddleware, because
    # TokenLoginMiddleware uses this to tell users they have been
    # automatically logged. It also has to come after
    # NoVarySessionMiddleware.
    'django.contrib.messages.middleware.MessageMiddleware',

    # This should come after MessageMiddleware
    'kitsune.sumo.middleware.SUMORefreshIDTokenAdminMiddleware',

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
    'kitsune.sumo.middleware.CacheHeadersMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'kitsune.sumo.anonymous.AnonymousIdentityMiddleware',
    'kitsune.sumo.middleware.ReadOnlyMiddleware',
    'kitsune.twitter.middleware.SessionMiddleware',
    'kitsune.sumo.middleware.PlusToSpaceMiddleware',
    'commonware.middleware.ScrubRequestOnException',
    'django_statsd.middleware.GraphiteRequestTimingMiddleware',
    'waffle.middleware.WaffleMiddleware',
    'commonware.middleware.RobotsTagHeader',
    # 'axes.middleware.FailedLoginMiddleware'
)

# SecurityMiddleware settings
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default='0', cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=not DEBUG, cast=bool)
SECURE_REDIRECT_EXEMPT = [
    r'^healthz/$',
    r'^readiness/$',
]
USE_X_FORWARDED_HOST = config('USE_X_FORWARDED_HOST', default=False, cast=bool)
if config('USE_SECURE_PROXY_HEADER', default=SECURE_SSL_REDIRECT, cast=bool):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# watchman
WATCHMAN_DISABLE_APM = config('WATCHMAN_DISABLE_APM', default=False, cast=bool)
WATCHMAN_CHECKS = (
    'watchman.checks.caches',
    'watchman.checks.databases',
)

# Auth
AUTHENTICATION_BACKENDS = (
    'kitsune.users.auth.SumoOIDCAuthBackend',
    # ``ModelBackendAllowInactive`` replaces ``django.contrib.auth.backends.ModelBackend``.
    'kitsune.users.auth.FXAAuthBackend',
    # This backend is used for the /admin interface
    'kitsune.users.auth.ModelBackendAllowInactive',
    'kitsune.users.auth.TokenLoginBackend',
)
if READ_ONLY:
    AUTHENTICATION_BACKENDS = ('kitsune.sumo.readonlyauth.ReadOnlyBackend',)
    OIDC_ENABLE = False
    ENABLE_ADMIN = False
else:
    OIDC_ENABLE = config('OIDC_ENABLE', default=True, cast=bool)
    ENABLE_ADMIN = config('ENABLE_ADMIN', default=OIDC_ENABLE, cast=bool)

    # Username algo for the oidc lib
    def _username_algo(email):
        """Provide a default username for the user."""
        from kitsune.users.utils import suggest_username
        return suggest_username(email)

    if OIDC_ENABLE:
        OIDC_OP_AUTHORIZATION_ENDPOINT = config('OIDC_OP_AUTHORIZATION_ENDPOINT', default='')
        OIDC_OP_TOKEN_ENDPOINT = config('OIDC_OP_TOKEN_ENDPOINT', default='')
        OIDC_OP_USER_ENDPOINT = config('OIDC_OP_USER_ENDPOINT', default='')
        OIDC_RP_CLIENT_ID = config('OIDC_RP_CLIENT_ID', default='')
        OIDC_RP_CLIENT_SECRET = config('OIDC_RP_CLIENT_SECRET', default='')
        OIDC_CREATE_USER = config('OIDC_CREATE_USER', default=False, cast=bool)
        # Exempt Firefox Accounts urls
        OIDC_EXEMPT_URLS = [
            'users.fxa_authentication_init',
            'users.fxa_authentication_callback',
            'users.fxa_logout_url',
        ]
        # Firefox Accounts configuration
        FXA_OP_TOKEN_ENDPOINT = config('FXA_OP_TOKEN_ENDPOINT', default='')
        FXA_OP_AUTHORIZATION_ENDPOINT = config('FXA_OP_AUTHORIZATION_ENDPOINT', default='')
        FXA_OP_USER_ENDPOINT = config('FXA_OP_USER_ENDPOINT', default='')
        FXA_OP_JWKS_ENDPOINT = config('FXA_OP_JWKS_ENDPOINT', default='')
        FXA_RP_CLIENT_ID = config('FXA_RP_CLIENT_ID', default='')
        FXA_RP_CLIENT_SECRET = config('FXA_RP_CLIENT_SECRET', default='')
        FXA_CREATE_USER = config('FXA_CREATE_USER', default=True, cast=bool)
        FXA_RP_SCOPES = config('FXA_RP_SCOPES', default='openid email profile')
        FXA_RP_SIGN_ALGO = config('FXA_RP_SIGN_ALGO', default='RS256')
        FXA_USE_NONCE = config('FXA_USE_NONCE', False)
        FXA_LOGOUT_REDIRECT_URL = config('FXA_LOGOUT_REDIRECT_URL', '/')
        FXA_USERNAME_ALGO = config('FXA_USERNAME_ALGO', default=_username_algo)
        FXA_STORE_ACCESS_TOKEN = config('FXA_STORE_ACCESS_TOKEN', default=False)

ADMIN_REDIRECT_URL = config('ADMIN_REDIRECT_URL', default=None)

AUTH_PROFILE_MODULE = 'users.Profile'
USER_AVATAR_PATH = 'uploads/avatars/'
DEFAULT_AVATAR = 'sumo/img/avatar.png'
AVATAR_SIZE = 48  # in pixels
MAX_AVATAR_FILE_SIZE = 131072  # 100k, in bytes
GROUP_AVATAR_PATH = 'uploads/groupavatars/'

ACCOUNT_ACTIVATION_DAYS = 30

PASSWORD_HASHERS = (
    'kitsune.users.hashers.SHA256PasswordHasher',
)

USERNAME_BLACKLIST = path('kitsune', 'configs', 'username-blacklist.txt')

ROOT_URLCONF = '%s.urls' % PROJECT_MODULE

# TODO: Figure out why changing the order of apps (for example, moving
# taggit higher in the list) breaks tests.
INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mozilla_django_oidc',
    'corsheaders',
    'kitsune.users',
    'dennis.django_dennis',
    'puente',
    'pipeline',
    'authority',
    'waffle',
    'storages',
    'kitsune.access',
    'kitsune.sumo',
    'kitsune.search',
    'kitsune.forums',
    'djcelery',
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
    'kitsune.journal',
    'kitsune.motidings',
    'rest_framework',
    'statici18n',
    'watchman',
    # 'axes',

    # Extra apps for testing.
    'django_nose',

    # Extra app for python migrations.
    'django_extensions',

    # In Django <= 1.6, this "must be placed somewhere after all the apps that
    # are going to be generating activities". Putting it at the end is the safest.
    'actstream',

    # Last so we can override admin templates.
    'django.contrib.admin',
)

TEST_RUNNER = 'kitsune.sumo.tests.TestSuiteRunner'


def JINJA_CONFIG():
    config = {
        'extensions': [
            'puente.ext.i18n',
        ],
        'finalize': lambda x: x if x is not None else '',
        'autoescape': True,
    }

    return config

# Tells the extract script what files to look for l10n in and what
# function handles the extraction. Puente expects this.
PUENTE = {
    'BASE_DIR': ROOT,
    'DOMAIN_METHODS': {
        'django': [
            ('kitsune/forums/**.py', 'ignore'),
            ('kitsune/forums/**.html', 'ignore'),
            ('kitsune/**/tests/**.py', 'ignore'),
            ('kitsune/**/management/**.py', 'ignore'),
            ('kitsune/forums/**.lhtml', 'ignore'),

            ('kitsune/**.py', 'python'),
            ('kitsune/**/templates/**.html', 'jinja2'),
            ('kitsune/**/jinja2/**.html', 'jinja2'),
            ('kitsune/**/jinja2/**.lhtml', 'jinja2'),
            ('kitsune/**/jinja2/**.ltxt', 'jinja2'),
            ('vendor/src/django-tidings/**/templates/**.html', 'jinja2'),
        ],
        'djangojs': [
            # We can't say **.js because that would dive into any libraries.
            ('kitsune/**/static/**/js/*-all.js', 'ignore'),
            ('kitsune/**/static/**/js/*-min.js', 'ignore'),

            ('kitsune/**/static/**/js/*.js', 'javascript'),
            ('kitsune/**/static/**/tpl/**.html', 'jinja2'),
        ],
    }
}

# These domains will not be merged into messages.pot and will use
# separate PO files. See the following URL for an example of how to
# set these domains in DOMAIN_METHODS.
# http://github.com/jbalogh/zamboni/blob/d4c64239c24aa2f1e91276909823d1d1b290f0ee/settings.py#L254 # nopep8
STANDALONE_DOMAINS = [
    TEXT_DOMAIN,
    'djangojs',
    'yaocho',
]

STATICI18N_DOMAIN = 'djangojs'
STATICI18N_PACKAGES = ['kitsune.sumo']
# Save jsi18n files outside of static so that collectstatic will pick
# them up and save it with hashed filenames in the static directory.
STATICI18N_ROOT = path('jsi18n')

#
# Django Pipline
PIPELINE = {
    'COMPILERS': (
        'pipeline.compilers.less.LessCompiler',
        'kitsune.lib.pipeline_compilers.BrowserifyCompiler',
    ),
    'JAVASCRIPT': PIPELINE_JS,
    'STYLESHEETS': PIPELINE_CSS,

    'DISABLE_WRAPPER': True,

    'JS_COMPRESSOR': 'pipeline.compressors.uglifyjs.UglifyJSCompressor',
    'UGLIFYJS_BINARY': path('node_modules/.bin/uglifyjs'),
    'UGLIFYJS_ARGUMENTS': '-r "\$super"',

    'CSS_COMPRESSOR': 'pipeline.compressors.cssmin.CSSMinCompressor',
    'CSSMIN_BINARY': path('node_modules/.bin/cssmin'),

    'LESS_BINARY': path('node_modules/.bin/lessc'),
    # TODO: Cannot make less work with autoprefix plugin
    # 'LESS_ARGUMENTS': '--autoprefix="> 1%, last 2 versions, ff > 1"',

    'BROWSERIFY_BINARY': path('node_modules/.bin/browserify'),
    'BROWSERIFY_ARGUMENTS': '-t babelify -t debowerify',
    'PIPELINE_COLLECTOR_ENABLED': config(
        'PIPELINE_COLLECTOR_ENABLED',
        default=not DEBUG,
        cast=bool,
    ),
}

if DEBUG:
    PIPELINE['BROWSERIFY_ARGUMENTS'] += ' -d'

NUNJUCKS_PRECOMPILE_BIN = path('node_modules/.bin/nunjucks-precompile')

#
# Sessions
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=4 * 7 * 24 * 60 * 60, cast=int)  # 4 weeks
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=not DEBUG, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_NAME = 'session_id'
SESSION_ENGINE = config('SESSION_ENGINE', default='django.contrib.sessions.backends.cache')
SESSION_EXISTS_COOKIE = 'sumo_session'
SESSION_SERIALIZER = config('SESSION_SERIALIZER', default='django.contrib.sessions.serializers.PickleSerializer')

#
# Connection information for Elastic
ES_URLS = [config('ES_URLS', default="localhost:9200")]
# Indexes for reading
ES_INDEXES = {
    'default': config('ES_INDEXES_DEFAULT', default='default'),
    'non-critical': config('ES_INDEXES_NON_CRITICAL', default='non-critical'),
    'metrics': config('ES_INDEXES_METRICS', 'metrics'),
}
# Indexes for indexing--set this to ES_INDEXES if you want to read to
# and write to the same index.
ES_WRITE_INDEXES = ES_INDEXES
# This is prepended to index names to get the final read/write index
# names used by kitsune. This is so that you can have multiple
# environments pointed at the same ElasticSearch cluster and not have
# them bump into one another.
ES_INDEX_PREFIX = config('ES_INDEX_PREFIX', default='sumo')
# Keep indexes up to date as objects are made/deleted.
ES_LIVE_INDEXING = config('ES_LIVE_INDEXING', default=True, cast=bool)
# Timeout for querying requests
ES_TIMEOUT = 5
ES_USE_SSL = config('ES_USE_SSL', default=False, cast=bool)
ES_HTTP_AUTH = config('ES_HTTP_AUTH', default='', cast=Csv())

SEARCH_MAX_RESULTS = 1000
SEARCH_RESULTS_PER_PAGE = 10

# Search default settings
SEARCH_DEFAULT_CATEGORIES = (10, 20,)
SEARCH_DEFAULT_MAX_QUESTION_AGE = 180 * 24 * 60 * 60  # seconds

# IA default settings
IA_DEFAULT_CATEGORIES = (10, 20,)

# The length for which we would like the user to cache search forms
# and results, in minutes.
SEARCH_CACHE_PERIOD = config('SEARCH_CACHE_PERIOD', default=15, cast=int)

# Maximum length of the filename. Forms should use this and raise
# ValidationError if the length is exceeded.
# @see http://code.djangoproject.com/ticket/9893
# Columns are 250 but this leaves 50 chars for the upload_to prefix
MAX_FILENAME_LENGTH = 200
MAX_FILEPATH_LENGTH = 250
# Default storage engine - ours does not preserve filenames
DEFAULT_FILE_STORAGE = 'kitsune.upload.storage.RenameFileStorage'

# AWS S3 Storage Settings
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default='')
AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default='user-media-prod-cdn.itsre-sumo.mozilla.net')
AWS_S3_HOST = config('AWS_S3_HOST', default='s3-us-west-2.amazonaws.com')
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=2592000',
}

# Auth and permissions related constants
LOGIN_URL = '/users/login'
LOGOUT_URL = '/users/logout'
LOGIN_REDIRECT_URL = "/"
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

# Badges (kbadge)
BADGE_IMAGE_PATH = 'uploads/badges/'

# Email
EMAIL_BACKEND = config('EMAIL_BACKEND', default='kitsune.lib.email.LoggingEmailBackend')
EMAIL_LOGGING_REAL_BACKEND = config('EMAIL_LOGGING_REAL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_SUBJECT_PREFIX = config('EMAIL_SUBJECT_PREFIX', default='[support] ')
if EMAIL_LOGGING_REAL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend':
    EMAIL_HOST = config('EMAIL_HOST')
    EMAIL_HOST_USER = config('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
    EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
    EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)


# Celery
djcelery.setup_loader()

CELERY_IGNORE_RESULT = config('CELERY_IGNORE_RESULT', default=True, cast=bool)
if not CELERY_IGNORE_RESULT:
    # E.g. redis://localhost:6479/1
    CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')

CELERY_ALWAYS_EAGER = config('CELERY_ALWAYS_EAGER', default=DEBUG, cast=bool)  # For tests. Set to False for use.
if not CELERY_ALWAYS_EAGER:
    BROKER_URL = config('BROKER_URL')

CELERY_SEND_TASK_ERROR_EMAILS = config('CELERY_SEND_TASK_ERROR_EMAILS', default=True, cast=bool)
CELERYD_LOG_LEVEL = config('CELERYD_LOG_LEVEL', default='INFO', cast=lambda x: getattr(logging, x))
CELERYD_CONCURRENCY = config('CELERYD_CONCURRENCY', default=4, cast=int)
CELERY_EAGER_PROPAGATES_EXCEPTIONS = config('CELERY_EAGER_PROPAGATES_EXCEPTIONS', default=True, cast=bool)  # Explode loudly during tests.
CELERYD_HIJACK_ROOT_LOGGER = config('CELERYD_HIJACK_ROOT_LOGGER', default=False, cast=bool)

# Wiki rebuild settings
WIKI_REBUILD_TOKEN = 'sumo:wiki:full-rebuild'

# Anonymous user cookie
ANONYMOUS_COOKIE_NAME = config('ANONYMOUS_COOKIE_NAME', default='SUMO_ANONID')
ANONYMOUS_COOKIE_MAX_AGE = config('ANONYMOUS_COOKIE_MAX_AGE', default=30 * 86400, cast=int) # One month

# Do not change this without also deleting all wiki documents:
WIKI_DEFAULT_LANGUAGE = LANGUAGE_CODE

# Gallery settings
GALLERY_DEFAULT_LANGUAGE = WIKI_DEFAULT_LANGUAGE
GALLERY_IMAGE_PATH = 'uploads/gallery/images/'
GALLERY_IMAGE_THUMBNAIL_PATH = 'uploads/gallery/images/thumbnails/'
GALLERY_VIDEO_PATH = 'uploads/gallery/videos/'
GALLERY_VIDEO_URL = MEDIA_URL + 'uploads/gallery/videos/'
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
    'pocket',  # bug 1164008
    'vagina',
    'slut',
]

BITLY_API_URL = config('BITLY_API_URL', default='http://api.bitly.com/v3/shorten?callback=?')
BITLY_LOGIN = config('BITLY_LOGIN', default=None)
BITLY_API_KEY = config('BITLY_API_KEY', default=None)

TWITTER_COOKIE_SECURE = config('TWITTER_COOKIE_SECURE', default=True, cast=bool)
TWITTER_CONSUMER_KEY = config('TWITTER_CONSUMER_KEY', default='')
TWITTER_CONSUMER_SECRET = config('TWITTER_CONSUMER_SECRET', default='')
TWITTER_ACCESS_TOKEN = config('TWITTER_ACCESS_TOKEN', default='')
TWITTER_ACCESS_TOKEN_SECRET = config('TWITTER_ACCESS_TOKEN_SECRET', default='')

TIDINGS_FROM_ADDRESS = config('TIDINGS_FROM_ADDRESS', default='notifications@support.mozilla.org')
# Anonymous watches must be confirmed.
TIDINGS_CONFIRM_ANONYMOUS_WATCHES = config('TIDINGS_CONFIRM_ANONYMOUS_WATCHES', default=True, cast=bool)
TIDINGS_MODEL_BASE = 'kitsune.sumo.models.ModelBase'
TIDINGS_REVERSE = 'kitsune.sumo.urlresolvers.reverse'


# Google Analytics settings.
# GA_KEY is expected b64 encoded.
GA_KEY = config('GA_KEY', default=None)  # Google API client key
if GA_KEY:
    import base64
    GA_KEY = base64.b64decode(GA_KEY)
GA_ACCOUNT = config('GA_ACCOUNT', 'something@developer.gserviceaccount.com')  # Google API Service Account email address
GA_PROFILE_ID = config('GA_PROFILE_ID', default='12345678')  # Google Analytics profile id for SUMO prod
GA_START_DATE = date(2012, 11, 10)
GTM_CONTAINER_ID = config('GTM_CONTAINER_ID', default='')  # Google container ID

MOBILE_COOKIE = config('MOBILE_COOKIE', default='msumo')

# Key to access /services/version. Set to None to disallow.
VERSION_CHECK_TOKEN = config('VERSION_CHECK_TOKEN', default=None)

REDIS_BACKENDS = {
    # TODO: Make sure that db number is respected
    'default': config('REDIS_DEFAULT_URL'),
    'helpfulvotes': config('REDIS_HELPFULVOTES_URL'),
}

HELPFULVOTES_UNHELPFUL_KEY = 'helpfulvotes_topunhelpful'

LAST_SEARCH_COOKIE = 'last_search'

OPTIPNG_PATH = config('OPTIPNG_PATH', default='/usr/bin/optipng')

# Zendesk info. Fill in the prefix, email and password in settings_local.py.
ZENDESK_URL = config('ZENDESK_URL', default='https://appsmarket.zendesk.com')
ZENDESK_SUBJECT_PREFIX = config('ZENDESK_SUBJECT_PREFIX', default='')
ZENDESK_USER_EMAIL = config('ZENDESK_USER_EMAIL', default='')
ZENDESK_USER_PASSWORD = config('ZENDESK_USER_PASSWORD', default='')

# Tasty Pie
API_LIMIT_PER_PAGE = 0

# Change the default for XFrameOptionsMiddleware.
X_FRAME_OPTIONS = 'DENY'

# Where to find the about:support troubleshooting addon.
# This is a link to the latest version, whatever that may be.
TROUBLESHOOTER_ADDON_URL = config(
    'TROUBLESHOOTER_ADDON_URL',
    default='https://addons.mozilla.org/firefox/downloads/latest/426841/addon-426841-latest.xpi')

# SurveyGizmo API
SURVEYGIZMO_USER = config('SURVEYGIZMO_USER', default=None)
SURVEYGIZMO_PASSWORD = config('SURVEYGIZMO_PASSWORD', default=None)
SURVEYGIZMO_API_TOKEN = config('SURVEYGIZMO_API_TOKEN', default=None)
SURVEYGIZMO_API_TOKEN_SECRET = config('SURVEYGIZMO_API_TOKEN_SECRET', default=None)

# Django Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
        'kitsune.sumo.api_utils.InactiveSessionAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'kitsune.sumo.api_utils.JSONRenderer',
    ),
    'UNICODE_JSON': False,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}

# Django-axes settings.
AXES_LOGIN_FAILURE_LIMIT = config('AXES_LOGIN_FAILURE_LIMIT', default=10, cast=int)
AXES_LOCK_OUT_AT_FAILURE = config('AXES_LOCK_OUT_AT_FAILURE', default=True, cast=bool)
AXES_USE_USER_AGENT = config('AXES_USE_USER_AGENT', default=False, cast=bool)
AXES_COOLOFF_TIME = config('AXES_COOLOFF_TIME', default=1, cast=int)  # hour
AXES_BEHIND_REVERSE_PROXY = config('AXES_BEHIND_REVERSE_PROXY', default=not DEBUG, cast=bool)
AXES_REVERSE_PROXY_HEADER = config('AXES_REVERSE_PROXY_HEADER', default='HTTP_X_CLUSTER_CLIENT_IP')

USE_DEBUG_TOOLBAR = config('USE_DEBUG_TOOLBAR', default=False, cast=bool)

# Set this to True to wrap each HTTP request in a transaction on this database.
ATOMIC_REQUESTS = config('ATOMIC_REQUESTS', default=True, cast=bool)

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
    r'^/api/2/notification/.*$',
    r'^/api/2/question/.*$',
    r'^/api/2/realtime/.*$',
    r'^/api/2/search/.*$',
    r'^/api/2/user/.*$',
]
# Now combine all those regexes with one big "or".
CORS_URLS_REGEX = re.compile('|'.join('({0})'.format(r) for r in CORS_URLS_REGEX))

# XXX Fix this when Bug 1059545 is fixed
CC_IGNORE_USERS = []

ACTSTREAM_SETTINGS = {
    'USE_JSONFIELD': True,
}

SILENCED_SYSTEM_CHECKS = [
    'fields.W340',  # null has no effect on ManyToManyField.
    'fields.W342',  # ForeignKey(unique=True) is usually better served by a OneToOneField
]

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
ALLOWED_CIDR_NETS = config('ALLOWED_CIDR_NETS', default='', cast=Csv())
# in production set this to 'support.mozilla.org' and all other domains will redirect.
# can be a comma separated list of allowed domains.
# the first in the list will be the target of redirects.
# needs to be None if not set so that the middleware will
# be turned off. can't set default to None because of the Csv() cast.
ENFORCE_HOST = config('ENFORCE_HOST', default='', cast=Csv()) or None

# Allows you to specify waffle settings in the querystring.
WAFFLE_OVERRIDE = config('WAFFLE_OVERRIDE', default=DEBUG, cast=bool)

STATSD_CLIENT = config('STATSD_CLIENT', 'django_statsd.clients.null')
STATSD_HOST = config('STATSD_HOST', default='localhost')
STATSD_PORT = config('STATSD_PORT', 8125, cast=int)
STATSD_PREFIX = config('STATSD_PREFIX', default='')


if config('SENTRY_DSN', None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    # see https://docs.sentry.io/learn/filtering/?platform=python
    def filter_exceptions(event, hint):
        # Ignore errors from specific loggers.
        if event.get('logger', '') == 'django.security.DisallowedHost':
            return None

        return event

    sentry_sdk.init(
        dsn=config('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        release=config('GIT_SHA', default=None),
        server_name=PLATFORM_NAME,
        environment=config('SENTRY_ENVIRONMENT', default=''),
        before_send=filter_exceptions,
    )


PIPELINE_ENABLED = config('PIPELINE_ENABLED', default=False, cast=bool)

# Dead Man Snitches
DMS_ENQUEUE_LAG_MONITOR_TASK = config('DMS_ENQUEUE_LAG_MONITOR_TASK', default=None)
DMS_SEND_WELCOME_EMAILS = config('DMS_SEND_WELCOME_EMAILS', default=None)
DMS_UPDATE_PRODUCT_DETAILS = config('DMS_UPDATE_PRODUCT_DETAILS', default=None)
DMS_GENERATE_MISSING_SHARE_LINKS = config('DMS_GENERATE_MISSING_SHARE_LINKS', default=None)
DMS_REBUILD_KB = config('DMS_REBUILD_KB', default=None)
DMS_UPDATE_TOP_CONTRIBUTORS = config('DMS_UPDATE_TOP_CONTRIBUTORS', default=None)
DMS_UPDATE_L10N_COVERAGE_METRICS = config('DMS_UPDATE_L10N_COVERAGE_METRICS', default=None)
DMS_CALCULATE_CSAT_METRICS = config('DMS_CALCULATE_CSAT_METRICS', default=None)
DMS_REPORT_EMPLOYEE_ANSWERS = config('DMS_REPORT_EMPLOYEE_ANSWERS', default=None)
DMS_REINDEX_USERS_THAT_CONTRIBUTED_YESTERDAY = config('DMS_REINDEX_USERS_THAT_CONTRIBUTED_YESTERDAY', default=None)
DMS_UPDATE_WEEKLY_VOTES = config('DMS_UPDATE_WEEKLY_VOTES', default=None)
DMS_UPDATE_SEARCH_CTR_METRIC = config('DMS_UPDATE_SEARCH_CTR_METRIC', default=None)
DMS_REMOVE_EXPIRED_REGISTRATION_PROFILES = config('DMS_REMOVE_EXPIRED_REGISTRATION_PROFILES', default=None)
DMS_UPDATE_CONTRIBUTOR_METRICS = config('DMS_UPDATE_CONTRIBUTOR_METRICS', default=None)
DMS_AUTO_ARCHIVE_OLD_QUESTIONS = config('DMS_AUTO_ARCHIVE_OLD_QUESTIONS', default=None)
DMS_REINDEX = config('DMS_REINDEX', default=None)
DMS_PROCESS_EXIT_SURVEYS = config('DMS_PROCESS_EXIT_SURVEYS', default=None)
DMS_SURVEY_RECENT_ASKERS = config('DMS_SURVEY_RECENT_ASKERS', default=None)
DMS_CLEAR_EXPIRED_AUTH_TOKENS = config('DMS_CLEAR_EXPIRED_AUTH_TOKENS', default=None)
# DMS_UPDATE_VISITORS_METRIC = config('DMS_UPDATE_VISITORS_METRIC', default=None)
DMS_UPDATE_L10N_METRIC = config('DMS_UPDATE_L10N_METRIC', default=None)
DMS_RELOAD_WIKI_TRAFFIC_STATS = config('DMS_RELOAD_WIKI_TRAFFIC_STATS', default=None)
DMS_CACHE_MOST_UNHELPFUL_KB_ARTICLES = config('DMS_CACHE_MOST_UNHELPFUL_KB_ARTICLES', default=None)
DMS_RELOAD_QUESTION_TRAFFIC_STATS = config('DMS_RELOAD_QUESTION_TRAFFIC_STATS', default=None)
DMS_PURGE_HASHES = config('DMS_PURGE_HASHES', default=None)
DMS_SEND_WEEKLY_READY_FOR_REVIEW_DIGEST = config('DMS_SEND_WEEKLY_READY_FOR_REVIEW_DIGEST', default=None)
DMS_FIX_CURRENT_REVISIONS = config('DMS_FIX_CURRENT_REVISIONS', default=None)
DMS_COHORT_ANALYSIS = config('DMS_COHORT_ANALYSIS', default=None)
DMS_UPDATE_L10N_CONTRIBUTOR_METRICS = config('DMS_UPDATE_L10N_CONTRIBUTOR_METRICS', default=None)

PROD_DETAILS_CACHE_NAME = 'product-details'
PROD_DETAILS_STORAGE = config('PROD_DETAILS_STORAGE',
                              default='product_details.storage.PDDatabaseStorage')

DISABLE_HOSTNAME_MIDDLEWARE = config('DISABLE_HOSTNAME_MIDDLEWARE', default=False, cast=bool)

DISABLE_FEEDS = config('DISABLE_FEEDS', default=False, cast=bool)
DISABLE_QUESTIONS_LIST_GLOBAL = config('DISABLE_QUESTIONS_LIST_GLOBAL', default=False, cast=bool)
DISABLE_QUESTIONS_LIST_ALL = config('DISABLE_QUESTIONS_LIST_ALL', default=False, cast=bool)
IMAGE_ATTACHMENT_USER_LIMIT = config('IMAGE_ATTACHMENT_USER_LIMIT', default=50, cast=int)

# list of strings to match against user agent to block
USER_AGENT_FILTERS = config('USER_AGENT_FILTERS', default='', cast=Csv())

BADGE_LIMIT_ARMY_OF_AWESOME = config('BADGE_LIMIT_ARMY_OF_AWESOME', default=50, cast=int)
BADGE_LIMIT_L10N_KB = config('BADGE_LIMIT_L10N_KB', default=10, cast=int)
BADGE_LIMIT_SUPPORT_FORUM = config('BADGE_LIMIT_SUPPORT_FORUM', default=30, cast=int)
BADGE_MAX_RECENT = config('BADGE_MAX_RECENT', default=15, cast=int)
BADGE_PAGE_SIZE = config('BADGE_PAGE_SIZE', default=50, cast=int)

# fxa banner test
FXA_BANNER_LANGUAGES = config('FXA_BANNER_LANGUAGES', default='en-US', cast=Csv())

# The canonical, production URL without a trailing slash
CANONICAL_URL = 'https://support.mozilla.org'
