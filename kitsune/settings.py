# -*- coding: utf-8 -*-
"""Django settings for kitsune project."""

import logging
import os
import platform
import re

import dj_database_url
import django_cache_url
import pymysql
from decouple import Csv, config

from kitsune.lib.sumo_locales import LOCALES

DEBUG = config("DEBUG", default=False, cast=bool)
DEV = config("DEV", default=False, cast=bool)
TEST = config("TEST", default=False, cast=bool)
STAGE = config("STAGE", default=False, cast=bool)

# TODO
# LOG_LEVEL = config('LOG_LEVEL', default='INFO', cast=labmda x: getattr(logging, x))
LOG_LEVEL = config("LOG_LEVEL", default=logging.INFO)

SYSLOG_TAG = "http_sumo_app"

# Repository directory.
ROOT = os.path.dirname(os.path.dirname(__file__))

# Django project directory.
PROJECT_ROOT = os.path.dirname(__file__)

PROJECT_MODULE = "kitsune"


# path bases things off of ROOT
def path(*parts):
    return os.path.abspath(os.path.join(ROOT, *parts))


# Read-only mode setup.
READ_ONLY = config("READ_ONLY", default=False, cast=bool)
ENABLE_VARY_NOCACHE_MIDDLEWARE = config(
    "ENABLE_VARY_NOCACHE_MIDDLEWARE", default=READ_ONLY, cast=bool
)

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
        assert value.lower() == "persistent", 'Must be int or "persistent"'
        return None


DB_CONN_MAX_AGE = config("DB_CONN_MAX_AGE", default=60, cast=parse_conn_max_age)

DATABASES = {
    "default": config("DATABASE_URL", cast=dj_database_url.parse),
}

if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":
    DATABASES["default"]["CONN_MAX_AGE"] = DB_CONN_MAX_AGE
    DATABASES["default"]["OPTIONS"] = {"init_command": "SET default_storage_engine=InnoDB"}

pymysql.install_as_MySQLdb()

# Cache Settings
CACHES = {
    "default": config("CACHE_URL", default="locmem://", cast=django_cache_url.parse),
    "product-details": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "product-details",
        "OPTIONS": {
            "MAX_ENTRIES": 200,  # currently 104 json files
            "CULL_FREQUENCY": 4,  # 1/4 entries deleted if max reached
        },
    },
}
CACHE_SHORT_TIMEOUT = config("CACHE_SHORT_TIMEOUT", cast=int, default=60 * 60)  # 1 hour
CACHE_MEDIUM_TIMEOUT = config("CACHE_MEDIUM_TIMEOUT", cast=int, default=60 * 60 * 3)  # 3 hours
CACHE_LONG_TIMEOUT = config("CACHE_LONG_TIMEOUT", cast=int, default=60 * 60 * 24)  # 24 hours

CACHE_MIDDLEWARE_SECONDS = config(
    "CACHE_MIDDLEWARE_SECONDS", default=(2 * 60 * 60) if READ_ONLY else 0, cast=int
)

# Setting this to the Waffle version.
WAFFLE_CACHE_PREFIX = "w2.1:"
# User agent cache settings
USER_AGENTS_CACHE = "default"
# Addresses email comes from
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="notifications@support.mozilla.org")
DEFAULT_REPLY_TO_EMAIL = config("DEFAULT_REPLY_TO_EMAIL", default="no-reply@mozilla.org")
SERVER_EMAIL = config("SERVER_EMAIL", default="server-error@support.mozilla.org")

PLATFORM_NAME = platform.node()
K8S_DOMAIN = config("K8S_DOMAIN", default="")

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = config("TIME_ZONE", default="US/Pacific")

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-US"

# Supported languages
# Note: We periodically add locales to this list and it is easier to
# review with changes with one locale per line.
SUMO_LANGUAGES = (
    "af",
    "ar",
    "az",
    "bg",
    "bm",
    "bn",
    "bs",
    "ca",
    "cs",
    "da",
    "de",
    "ee",
    "el",
    "en-US",
    "es",
    "et",
    "eu",
    "fa",
    "fi",
    "fr",
    "fy-NL",
    "ga-IE",
    "gl",
    "gn",
    "gu-IN",
    "ha",
    "he",
    "hi-IN",
    "hr",
    "hu",
    "dsb",
    "hsb",
    "id",
    "ig",
    "it",
    "ja",
    "ka",
    "km",
    "kn",
    "ko",
    "ln",
    "lt",
    "mg",
    "mk",
    "ml",
    "ms",
    "ne-NP",
    "nl",
    "no",
    "pl",
    "pt-BR",
    "pt-PT",
    "ro",
    "ru",
    "si",
    "sk",
    "sl",
    "sq",
    "sr",
    "sw",
    "sv",
    "ta",
    "ta-LK",
    "te",
    "th",
    "tn",
    "tr",
    "uk",
    "ur",
    "vi",
    "wo",
    "xh",
    "xx",  # This is a test locale
    "yo",
    "zh-CN",
    "zh-TW",
    "zu",
)

# Modifies the locale to fallback to, for these locales.
# By default all locales (including the fallback locale)
# will fallback to en (unless it is also a key in this dict).
FALLBACK_LANGUAGES = {
    "fy-NL": "fy",
    "zh-CN": "zh-Hans",
    "zh-TW": "zh-Hant",
}

# These languages will get a wiki page instead of the product and topic pages.
SIMPLE_WIKI_LANGUAGES = [
    "az",
    "et",
    "ga-IE",
    "gl",
    "kn",
    "ml",
    "tn",
]

# Languages that should show up in language switcher.
LANGUAGE_CHOICES = tuple([(lang, LOCALES[lang].native) for lang in SUMO_LANGUAGES if lang != "xx"])
LANGUAGE_CHOICES_ENGLISH = tuple(
    [(lang, LOCALES[lang].english) for lang in SUMO_LANGUAGES if lang != "xx"]
)
LANGUAGES_DICT = dict([(i.lower(), LOCALES[i].native) for i in SUMO_LANGUAGES])
LANGUAGES = list(LANGUAGES_DICT.items())

LANGUAGE_URL_MAP = dict([(i.lower(), i) for i in SUMO_LANGUAGES])

# Locales that are known but unsupported. Keys are the locale, values
# are an optional fallback locale, or None, to use the LANGUAGE_CODE.
NON_SUPPORTED_LOCALES = {
    "ach": None,
    "ak": None,
    "an": "es",
    "as": None,
    "ast": "es",
    "be": "ru",
    "bn-BD": "bn",
    "bn-IN": "bn",
    "br": "fr",
    "cak": None,
    "csb": "pl",
    "co": None,
    "cy": None,
    "eo": None,
    "ff": None,
    "fur": "it",
    "gd": None,
    "hy-AM": None,
    "ilo": None,
    "ia": None,
    "in": "id",
    "is": None,
    "iw": "he",
    "iw-IL": "he",
    "kab": None,
    "kk": None,
    "lg": None,
    "lij": "it",
    "lo": None,
    "ltg": None,
    "lv": None,
    "mai": None,
    "mn": None,
    "mr": None,
    "my": None,
    "nb-NO": "no",
    "nn-NO": "no",
    "nso": None,
    "oc": "fr",
    "or": None,
    "pa-IN": None,
    "rm": None,
    "rw": None,
    "sah": None,
    "son": None,
    "su": None,
    "sv-SE": "sv",
    "tl": None,
    "uz": None,
}

ES_LOCALE_ANALYZERS = {
    "ar": "arabic",
    "bg": "bulgarian",
    "ca": "snowball-catalan",
    "cs": "czech",
    "da": "snowball-danish",
    "de": "snowball-german",
    "en-US": "snowball-english",
    "es": "snowball-spanish",
    "eu": "snowball-basque",
    "fa": "persian",
    "fi": "snowball-finnish",
    "fr": "snowball-french",
    "hi-IN": "hindi",
    "hu": "snowball-hungarian",
    "id": "indonesian",
    "it": "snowball-italian",
    "ja": "cjk",
    "nl": "snowball-dutch",
    "no": "snowball-norwegian",
    "pl": "polish",
    "pt-BR": "snowball-portuguese",
    "pt-PT": "snowball-portuguese",
    "ro": "snowball-romanian",
    "ru": "snowball-russian",
    "sv": "snowball-swedish",
    "th": "thai",
    "tr": "snowball-turkish",
    "zh-CN": "chinese",
    "zh-TW": "chinese",
}

ES_PLUGIN_ANALYZERS = ["polish"]

ES_USE_PLUGINS = config("ES_USE_PLUGINS", default=not DEBUG, cast=bool)

ES_BULK_DEFAULT_TIMEOUT = config("ES_BULK_DEFAULT_TIMEOUT", default=10, cast=float)
ES_BULK_MAX_RETRIES = config("ES_BULK_MAX_RETRIES", default=1, cast=int)

ES_DEFAULT_SQL_CHUNK_SIZE = config("ES_DEFAULT_SQL_CHUNK_SIZE", default=1000, cast=int)
ES_DEFAULT_ELASTIC_CHUNK_SIZE = config("ES_DEFAULT_ELASTIC_CHUNK_SIZE", default=50, cast=int)

TEXT_DOMAIN = "messages"

SITE_ID = 1

USE_I18N = True
USE_L10N = True

DB_LOCALIZE = {
    "karma": {
        "Title": {
            "attrs": ["name"],
            "comments": ["This is a karma title."],
        }
    },
    "products": {
        "Product": {
            "attrs": ["title", "description"],
        },
        "Topic": {
            "attrs": ["title", "description"],
        },
    },
    "kbadge": {
        "Badge": {
            "attrs": ["title", "description"],
        },
    },
}

# locale is in the kitsune git repo project directory, so that's
# up one directory from the PROJECT_ROOT
if config("SET_LOCALE_PATHS", default=True, cast=bool):
    LOCALE_PATHS = (path("locale"),)

# Use the real robots.txt?
ENGAGE_ROBOTS = config("ENGAGE_ROBOTS", default=not DEBUG, cast=bool)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path("media")
MEDIA_URL = config("MEDIA_URL", default="/media/")

STATIC_ROOT = path("static")
STATIC_URL = config("STATIC_URL", default="/static/")
STATICFILES_DIRS = (
    path("jsi18n"),  # Collect jsi18n so that it is cache-busted
    path("dist"),
)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


def immutable_file_test(path, url):
    return re.match(r"^.+\.[0-9a-f]{16}\..+$", url)


WHITENOISE_IMMUTABLE_FILE_TEST = immutable_file_test

WEBPACK_LRU_CACHE = 128
if DEV or TEST:
    WEBPACK_LRU_CACHE = 0

# Paths that don't require a locale prefix.
SUPPORTED_NONLOCALES = (
    "1",
    "admin",
    "api",
    "favicon.ico",
    "media",
    "postcrash",
    "robots.txt",
    "manifest.json",
    "services",
    "wafflejs",
    "geoip-suggestion",
    "contribute.json",
    "oidc",
    "healthz",
    "readiness",
    "__debug__",
    "graphql",
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = config("SECRET_KEY")

_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.template.context_processors.debug",
    "django.template.context_processors.media",
    "django.template.context_processors.static",
    "django.template.context_processors.request",
    "django.template.context_processors.i18n",
    "django.contrib.messages.context_processors.messages",
    "kitsune.sumo.context_processors.global_settings",
    "kitsune.sumo.context_processors.i18n",
    "kitsune.sumo.context_processors.aaq_languages",
    "kitsune.sumo.context_processors.current_year",
    "kitsune.sumo.context_processors.static_url_webpack",
    "kitsune.messages.context_processors.unread_message_count",
]

TEMPLATES = [
    {
        "BACKEND": "django_jinja.backend.Jinja2",
        "NAME": "jinja2",
        "DIRS": [
            path("dist"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            # Use jinja2/ for jinja templates
            "app_dirname": "jinja2",
            # Don't figure out which template loader to use based on
            # file extension
            "match_extension": "",
            "newstyle_gettext": True,
            "context_processors": _CONTEXT_PROCESSORS,
            "undefined": "jinja2.Undefined",
            "extensions": [
                "waffle.jinja.WaffleExtension",
                "jinja2.ext.do",
                "django_jinja.builtins.extensions.CsrfExtension",
                "django_jinja.builtins.extensions.StaticFilesExtension",
                "django_jinja.builtins.extensions.DjangoFiltersExtension",
                "jinja2.ext.i18n",
                'wagtail.jinja2tags.core',
                'wagtail.admin.jinja2tags.userbar',
                'wagtail.images.jinja2tags.images',
            ],
            "policies": {
                "ext.i18n.trimmed": True,
            },
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "debug": DEBUG,
            "context_processors": _CONTEXT_PROCESSORS,
        },
    },
]


MIDDLEWARE = (
    "kitsune.sumo.middleware.HostnameMiddleware",
    "allow_cidr.middleware.AllowCIDRMiddleware",
    "kitsune.sumo.middleware.FilterByUserAgentMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "commonware.request.middleware.SetRemoteAddrFromForwardedFor",
    "kitsune.sumo.middleware.EnforceHostIPMiddleware",
    # VaryNoCacheMiddleware must be above LocaleURLMiddleware
    # so that it can see the response has a vary on accept-language
    "kitsune.sumo.middleware.VaryNoCacheMiddleware",
    # LocaleURLMiddleware requires access to request.user. These two must be
    # loaded before the LocaleURLMiddleware
    "commonware.middleware.NoVarySessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # This has to come after NoVarySessionMiddleware.
    "django.contrib.messages.middleware.MessageMiddleware",
    # refresh middleware for Firefox Accounts
    "kitsune.sumo.middleware.ValidateAccessTokenMiddleware",
    # refresh middleware for the Admin interface - uses IAM
    "kitsune.sumo.middleware.SUMORefreshIDTokenAdminMiddleware",
    # LocaleURLMiddleware must be before any middleware that uses
    # sumo.urlresolvers.reverse() to add locale prefixes to URLs:
    # "kitsune.sumo.middleware.LocaleURLMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "kitsune.sumo.middleware.Forbidden403Middleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "kitsune.sumo.middleware.RemoveSlashMiddleware",
    "kitsune.inproduct.middleware.EuBuildMiddleware",
    "kitsune.sumo.middleware.CacheHeadersMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "kitsune.sumo.anonymous.AnonymousIdentityMiddleware",
    "kitsune.sumo.middleware.ReadOnlyMiddleware",
    "kitsune.sumo.middleware.PlusToSpaceMiddleware",
    "commonware.middleware.ScrubRequestOnException",
    "waffle.middleware.WaffleMiddleware",
    "commonware.middleware.RobotsTagHeader",
    # 'axes.middleware.FailedLoginMiddleware'
    "kitsune.sumo.middleware.InAAQMiddleware",
    "kitsune.users.middleware.LogoutDeactivatedUsersMiddleware",
    "kitsune.users.middleware.LogoutInvalidatedSessionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
)

# SecurityMiddleware settings
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default="0", cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_BROWSER_XSS_FILTER = config("SECURE_BROWSER_XSS_FILTER", default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config("SECURE_CONTENT_TYPE_NOSNIFF", default=True, cast=bool)
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=not DEBUG, cast=bool)
SECURE_REDIRECT_EXEMPT = [
    r"^healthz/$",
    r"^readiness/$",
]
USE_X_FORWARDED_HOST = config("USE_X_FORWARDED_HOST", default=False, cast=bool)
if config("USE_SECURE_PROXY_HEADER", default=SECURE_SSL_REDIRECT, cast=bool):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# watchman
WATCHMAN_DISABLE_APM = config("WATCHMAN_DISABLE_APM", default=False, cast=bool)
WATCHMAN_CHECKS = (
    "watchman.checks.caches",
    "watchman.checks.databases",
)

# Auth
AUTHENTICATION_BACKENDS = (
    # This backend is used for the /admin interface
    "kitsune.users.auth.SumoOIDCAuthBackend",
    "kitsune.users.auth.FXAAuthBackend",
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
)
if READ_ONLY:
    AUTHENTICATION_BACKENDS = ("kitsune.sumo.readonlyauth.ReadOnlyBackend",)
    OIDC_ENABLE = False
    ENABLE_ADMIN = False
else:
    OIDC_ENABLE = config("OIDC_ENABLE", default=True, cast=bool)
    ENABLE_ADMIN = config("ENABLE_ADMIN", default=OIDC_ENABLE, cast=bool)

    # Username algo for the oidc lib
    def _username_algo(email):
        """Provide a default username for the user."""
        from kitsune.users.utils import suggest_username

        return suggest_username(email)

    if OIDC_ENABLE:
        OIDC_OP_AUTHORIZATION_ENDPOINT = config("OIDC_OP_AUTHORIZATION_ENDPOINT", default="")
        OIDC_OP_TOKEN_ENDPOINT = config("OIDC_OP_TOKEN_ENDPOINT", default="")
        OIDC_OP_USER_ENDPOINT = config("OIDC_OP_USER_ENDPOINT", default="")
        OIDC_RP_CLIENT_ID = config("OIDC_RP_CLIENT_ID", default="")
        OIDC_RP_CLIENT_SECRET = config("OIDC_RP_CLIENT_SECRET", default="")
        OIDC_CREATE_USER = config("OIDC_CREATE_USER", default=False, cast=bool)
        # Exempt Firefox Accounts urls
        OIDC_EXEMPT_URLS = [
            "users.fxa_authentication_init",
            "users.fxa_authentication_callback",
            "users.fxa_logout_url",
            "users.fxa_webhook",
        ]
        # Firefox Accounts configuration
        FXA_OP_TOKEN_ENDPOINT = config("FXA_OP_TOKEN_ENDPOINT", default="")
        FXA_OP_AUTHORIZATION_ENDPOINT = config("FXA_OP_AUTHORIZATION_ENDPOINT", default="")
        FXA_OP_USER_ENDPOINT = config("FXA_OP_USER_ENDPOINT", default="")
        FXA_OP_SUBSCRIPTION_ENDPOINT = config("FXA_OP_SUBSCRIPTION_ENDPOINT", default="")
        FXA_OP_JWKS_ENDPOINT = config("FXA_OP_JWKS_ENDPOINT", default="")
        FXA_RP_CLIENT_ID = config("FXA_RP_CLIENT_ID", default="")
        FXA_RP_CLIENT_SECRET = config("FXA_RP_CLIENT_SECRET", default="")
        FXA_CREATE_USER = config("FXA_CREATE_USER", default=True, cast=bool)
        FXA_RP_SCOPES = config("FXA_RP_SCOPES", default="openid email profile")
        FXA_RP_SIGN_ALGO = config("FXA_RP_SIGN_ALGO", default="RS256")
        FXA_USE_NONCE = config("FXA_USE_NONCE", False)
        FXA_LOGOUT_REDIRECT_URL = config("FXA_LOGOUT_REDIRECT_URL", "/")
        FXA_USERNAME_ALGO = config("FXA_USERNAME_ALGO", default=_username_algo)
        FXA_STORE_ACCESS_TOKEN = config("FXA_STORE_ACCESS_TOKEN", default=True, cast=bool)
        FXA_STORE_ID_TOKEN = config("FXA_STORE_ID_TOKEN", default=False, cast=bool)
        FXA_SUBSCRIPTIONS = config(
            "FXA_SUBSCRIPTIONS", default="https://accounts.firefox.com/subscriptions"
        )
        FXA_SET_ISSUER = config("FXA_SET_ISSUER", default="https://accounts.firefox.com")
        FXA_VERIFY_URL = config(
            "FXA_VERIFY_URL", default="https://oauth.accounts.firefox.com/v1/verify"
        )
        # Defaults to 12 hours
        FXA_RENEW_ID_TOKEN_EXPIRY_SECONDS = config(
            "FXA_RENEW_ID_TOKEN_EXPIRY_SECONDS", default=43200, cast=int
        )

ADMIN_REDIRECT_URL = config("ADMIN_REDIRECT_URL", default=None)

# this allows logging in as any user, no password necessary
# never, ever, ever enable this on anything other than your local, firewalled, dev machine
ENABLE_DEV_LOGIN = config("ENABLE_DEV_LOGIN", default=False, cast=bool)

AUTH_PROFILE_MODULE = "users.Profile"
USER_AVATAR_PATH = "uploads/avatars/"
DEFAULT_AVATAR = "sumo/img/avatar.png"
AVATAR_SIZE = 200  # in pixels
MAX_AVATAR_FILE_SIZE = 1310720  # 1MB, in bytes
GROUP_AVATAR_PATH = "uploads/groupavatars/"

# Informs django-guardian that we don't want to enable object-level
# permissions for anonymous users.
ANONYMOUS_USER_NAME = None

ACCOUNT_ACTIVATION_DAYS = 30

PASSWORD_HASHERS = ("kitsune.users.hashers.SHA256PasswordHasher",)

USERNAME_BLACKLIST = path("kitsune", "configs", "username-blacklist.txt")

ROOT_URLCONF = "%s.urls" % PROJECT_MODULE

# TODO: Figure out why changing the order of apps (for example, moving
# taggit higher in the list) breaks tests.
INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "graphene_django",
    "mozilla_django_oidc",
    "corsheaders",
    "kitsune.users",
    "guardian",
    "waffle",
    "storages",
    "kitsune.access",
    "kitsune.sumo",
    "kitsune.search",
    "kitsune.forums",
    "rest_framework.authtoken",
    "kitsune.questions",
    "kitsune.kbadge",
    "taggit",
    "kitsune.flagit",
    "kitsune.upload",
    "product_details",
    "kitsune.wiki",
    "kitsune.kbforums",
    "kitsune.dashboards",
    "kitsune.gallery",
    "kitsune.customercare",
    "kitsune.inproduct",
    "kitsune.postcrash",
    "kitsune.landings",
    "kitsune.announcements",
    "kitsune.community",
    "kitsune.messages",
    "commonware.response.cookies",
    "kitsune.groups",
    "kitsune.karma",
    "kitsune.tags",
    "kitsune.kpi",
    "kitsune.products",
    "kitsune.notifications",
    "kitsune.journal",
    "kitsune.tidings",
    "rest_framework",
    "statici18n",
    "watchman",
    # 'axes',
    # Extra app for python migrations.
    "django_extensions",
    # In Django <= 1.6, this "must be placed somewhere after all the apps that
    # are going to be generating activities". Putting it at the end is the safest.
    "actstream",
    "django_user_agents",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.modeladmin",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail.locales",
    "wagtail",
    "modelcluster",
    # Last so we can override admin templates.
    "django.contrib.admin",
)


def JINJA_CONFIG():
    config = {
        "extensions": [
            "jinja2.ext.i18n",
        ],
        "finalize": lambda x: x if x is not None else "",
        "autoescape": True,
    }

    return config


# These domains will not be merged into messages.pot and will use
# separate PO files. See the following URL for an example of how to
# set these domains in DOMAIN_METHODS.
# http://github.com/jbalogh/zamboni/blob/d4c64239c24aa2f1e91276909823d1d1b290f0ee/settings.py#L254 # nopep8
STANDALONE_DOMAINS = [
    TEXT_DOMAIN,
    "djangojs",
]

STATICI18N_DOMAIN = "djangojs"
STATICI18N_PACKAGES = ["kitsune.sumo"]
# Save jsi18n files outside of static so that collectstatic will pick
# them up and save it with hashed filenames in the static directory.
STATICI18N_ROOT = path("jsi18n")

#
# Sessions
SESSION_COOKIE_AGE = config(
    "SESSION_COOKIE_AGE", default=4 * 7 * 24 * 60 * 60, cast=int
)  # 4 weeks
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=not DEBUG, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_NAME = "session_id"
SESSION_ENGINE = config("SESSION_ENGINE", default="django.contrib.sessions.backends.cache")
SESSION_SERIALIZER = config(
    "SESSION_SERIALIZER", default="django.contrib.sessions.serializers.PickleSerializer"
)

# CSRF
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=not DEBUG, cast=bool)
#
# Connection information for Elastic 7
ES_TIMEOUT = 5  # Timeout for querying requests
ES_URLS = config("ES_URLS", cast=Csv(), default="elasticsearch:9200")
ES_CLOUD_ID = config("ES_CLOUD_ID", default="")
ES_USE_SSL = config("ES_USE_SSL", default=False, cast=bool)
ES_HTTP_AUTH = config("ES_HTTP_AUTH", default="", cast=Csv())
ES_ENABLE_CONSOLE_LOGGING = config("ES_ENABLE_CONSOLE_LOGGING", default=False, cast=bool)
# Pass parameters to the ES client
# like "search_type": "dfs_query_then_fetch"
ES_SEARCH_PARAMS = {"request_timeout": ES_TIMEOUT}

# This is prepended to index names to get the final read/write index
# names used by kitsune. This is so that you can have multiple
# environments pointed at the same ElasticSearch cluster and not have
# them bump into one another.
ES_INDEX_PREFIX = config("ES_INDEX_PREFIX", default="sumo")
# Keep indexes up to date as objects are made/deleted.
ES_LIVE_INDEXING = config("ES_LIVE_INDEXING", default=True, cast=bool)

SEARCH_MAX_RESULTS = 1000
SEARCH_RESULTS_PER_PAGE = 10

# Search default settings
SEARCH_DEFAULT_CATEGORIES = (
    10,
    20,
)
SEARCH_DEFAULT_MAX_QUESTION_AGE = 180 * 24 * 60 * 60  # seconds

# IA default settings
IA_DEFAULT_CATEGORIES = (
    10,
    20,
    30,
)

# The length for which we would like the user to cache search forms
# and results, in minutes.
SEARCH_CACHE_PERIOD = config("SEARCH_CACHE_PERIOD", default=15, cast=int)

# Maximum length of the filename. Forms should use this and raise
# ValidationError if the length is exceeded.
# @see http://code.djangoproject.com/ticket/9893
# Columns are 250 but this leaves 50 chars for the upload_to prefix
MAX_FILENAME_LENGTH = 200
MAX_FILEPATH_LENGTH = 250
# Default storage engine - ours does not preserve filenames
DEFAULT_FILE_STORAGE = "kitsune.upload.storage.RenameFileStorage"

# GCP storage settings
GS_BUCKET_NAME = config("GS_BUCKET_NAME", default="")
GS_CUSTOM_ENDPOINT = config("MEDIA_URL", default="").rstrip("/")
GS_LOCATION = config("GS_LOCATION", default="media")
GS_QUERYSTRING_AUTH = config("GS_QUERYSTRING_AUTH", default=False, cast=bool)

# AWS S3 Storage Settings
AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_CUSTOM_DOMAIN = config(
    "AWS_S3_CUSTOM_DOMAIN", default="user-media-prod-cdn.itsre-sumo.mozilla.net"
)
AWS_S3_HOST = config("AWS_S3_HOST", default="s3-us-west-2.amazonaws.com")
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "max-age=2592000",
}
AWS_DEFAULT_ACL = config("AWS_DEFAULT_ACL", default=None)

# Auth and permissions related constants
LOGIN_URL = "/users/login"
LOGOUT_URL = "/users/logout"
LOGIN_REDIRECT_URL = "/"
REGISTER_URL = "/users/register"

# Video settings, hard coded here for now.
# TODO: figure out a way that doesn't need these values
WIKI_VIDEO_WIDTH = 640
WIKI_VIDEO_HEIGHT = 480

IMAGE_MAX_FILESIZE = 10485760  # 10 megabytes, in bytes
THUMBNAIL_SIZE = 120  # Thumbnail size, in pixels
THUMBNAIL_UPLOAD_PATH = "uploads/images/thumbnails/"
IMAGE_UPLOAD_PATH = "uploads/images/"
# A string listing image mime types to accept, comma separated.
# String must not contain double quotes!
IMAGE_ALLOWED_MIMETYPES = "image/jpeg,image/png,image/gif"

# Topics
TOPIC_IMAGE_PATH = "uploads/topics/"

# Products
PRODUCT_IMAGE_PATH = "uploads/products/"

# Badges (kbadge)
BADGE_IMAGE_PATH = "uploads/badges/"

# Email
EMAIL_BACKEND = config("EMAIL_BACKEND", default="kitsune.lib.email.LoggingEmailBackend")
EMAIL_LOGGING_REAL_BACKEND = config(
    "EMAIL_LOGGING_REAL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_SUBJECT_PREFIX = config("EMAIL_SUBJECT_PREFIX", default="[support] ")
if EMAIL_LOGGING_REAL_BACKEND == "django.core.mail.backends.smtp.EmailBackend":
    EMAIL_HOST = config("EMAIL_HOST")
    EMAIL_HOST_USER = config("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
    EMAIL_PORT = config("EMAIL_PORT", default=25, cast=int)
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=False, cast=bool)


# Celery
CELERY_TASK_PROTOCOL = 2
CELERY_TASK_SERIALIZER = config("CELERY_TASK_SERIALIZER", default="json")
CELERY_RESULT_SERIALIZER = config("CELERY_RESULT_SERIALIZER", default="json")
CELERY_TASK_IGNORE_RESULT = config("CELERY_TASK_IGNORE_RESULT", default=True, cast=bool)
if not CELERY_TASK_IGNORE_RESULT:
    # E.g. redis://localhost:6479/1
    CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND")

CELERY_TASK_ALWAYS_EAGER = config(
    "CELERY_TASK_ALWAYS_EAGER", default=DEBUG, cast=bool
)  # For tests. Set to False for use.
if not CELERY_TASK_ALWAYS_EAGER:
    CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="")

# TODO:PY3: Setting gone, use celery worker --loglevel flag.
# CELERYD_LOG_LEVEL = config('CELERYD_LOG_LEVEL', default='INFO', cast=lambda x: getattr(logging, x))
CELERY_WORKER_CONCURRENCY = config("CELERY_WORKER_CONCURRENCY", default=4, cast=int)
CELERY_TASK_EAGER_PROPAGATES = config(
    "CELERY_TASK_EAGER_PROPAGATES", default=True, cast=bool
)  # Explode loudly during tests.
CELERY_WORKER_HIJACK_ROOT_LOGGER = config(
    "CELERY_WORKER_HIJACK_ROOT_LOGGER", default=False, cast=bool
)

# Wiki rebuild settings
WIKI_REBUILD_TOKEN = "sumo:wiki:full-rebuild"

# Anonymous user cookie
ANONYMOUS_COOKIE_NAME = config("ANONYMOUS_COOKIE_NAME", default="SUMO_ANONID")
ANONYMOUS_COOKIE_MAX_AGE = config(
    "ANONYMOUS_COOKIE_MAX_AGE", default=30 * 86400, cast=int
)  # One month

# Do not change this without also deleting all wiki documents:
WIKI_DEFAULT_LANGUAGE = LANGUAGE_CODE

# Gallery settings
GALLERY_DEFAULT_LANGUAGE = WIKI_DEFAULT_LANGUAGE
GALLERY_IMAGE_PATH = "uploads/gallery/images/"
GALLERY_IMAGE_THUMBNAIL_PATH = "uploads/gallery/images/thumbnails/"
GALLERY_VIDEO_PATH = "uploads/gallery/videos/"
GALLERY_VIDEO_URL = MEDIA_URL + "uploads/gallery/videos/"
GALLERY_VIDEO_THUMBNAIL_PATH = "uploads/gallery/videos/thumbnails/"
GALLERY_VIDEO_THUMBNAIL_PROGRESS_URL = MEDIA_URL + "img/video-thumb.png"
THUMBNAIL_PROGRESS_WIDTH = 32  # width of the above image
THUMBNAIL_PROGRESS_HEIGHT = 32  # height of the above image
VIDEO_MAX_FILESIZE = 52428800  # 50 megabytes, in bytes

BITLY_API_URL = config("BITLY_API_URL", default="https://api-ssl.bitly.com/v4/shorten")
BITLY_GUID = config("BITLY_GUID", default="")
BITLY_ACCESS_TOKEN = config("BITLY_ACCESS_TOKEN", default="")

TIDINGS_FROM_ADDRESS = config("TIDINGS_FROM_ADDRESS", default="notifications@support.mozilla.org")
# Anonymous watches must be confirmed.
TIDINGS_CONFIRM_ANONYMOUS_WATCHES = config(
    "TIDINGS_CONFIRM_ANONYMOUS_WATCHES", default=True, cast=bool
)
TIDINGS_MODEL_BASE = "kitsune.sumo.models.ModelBase"
TIDINGS_REVERSE = "kitsune.sumo.urlresolvers.reverse"


# Google Analytics settings.
# GA_KEY is expected b64 encoded.
GA_KEY = config("GA_KEY", default=None)  # Google API client key
GA_ACCOUNT = config(
    "GA_ACCOUNT", "something@developer.gserviceaccount.com"
)  # Google API Service Account email address
GA_PROFILE_ID = config(
    "GA_PROFILE_ID", default="12345678"
)  # Google Analytics profile id for SUMO prod
GTM_CONTAINER_ID = config("GTM_CONTAINER_ID", default="")  # Google container ID

REDIS_BACKENDS = {
    # TODO: Make sure that db number is respected
    "default": config("REDIS_DEFAULT_URL"),
    "helpfulvotes": config("REDIS_HELPFULVOTES_URL"),
}

HELPFULVOTES_UNHELPFUL_KEY = "helpfulvotes_topunhelpful"

LAST_SEARCH_COOKIE = "last_search"

OPTIPNG_PATH = config("OPTIPNG_PATH", default="/usr/bin/optipng")

# Tasty Pie
API_LIMIT_PER_PAGE = 0

# Change the default for XFrameOptionsMiddleware.
X_FRAME_OPTIONS = "DENY"

# SurveyGizmo API
SURVEYGIZMO_USER = config("SURVEYGIZMO_USER", default=None)
SURVEYGIZMO_PASSWORD = config("SURVEYGIZMO_PASSWORD", default=None)
SURVEYGIZMO_API_TOKEN = config("SURVEYGIZMO_API_TOKEN", default=None)
SURVEYGIZMO_API_TOKEN_SECRET = config("SURVEYGIZMO_API_TOKEN_SECRET", default=None)

# Django Rest Framework
REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "kitsune.sumo.api_utils.InactiveSessionAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": ("kitsune.sumo.api_utils.JSONRenderer",),
    "UNICODE_JSON": False,
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

# Django-axes settings.
AXES_LOGIN_FAILURE_LIMIT = config("AXES_LOGIN_FAILURE_LIMIT", default=10, cast=int)
AXES_LOCK_OUT_AT_FAILURE = config("AXES_LOCK_OUT_AT_FAILURE", default=True, cast=bool)
AXES_USE_USER_AGENT = config("AXES_USE_USER_AGENT", default=False, cast=bool)
AXES_COOLOFF_TIME = config("AXES_COOLOFF_TIME", default=1, cast=int)  # hour
AXES_BEHIND_REVERSE_PROXY = config("AXES_BEHIND_REVERSE_PROXY", default=not DEBUG, cast=bool)
AXES_REVERSE_PROXY_HEADER = config("AXES_REVERSE_PROXY_HEADER", default="HTTP_X_CLUSTER_CLIENT_IP")

USE_DEBUG_TOOLBAR = config("USE_DEBUG_TOOLBAR", default=False, cast=bool)


def show_toolbar_callback(*args):
    return DEBUG and USE_DEBUG_TOOLBAR


SHOW_DEBUG_TOOLBAR = show_toolbar_callback()

if SHOW_DEBUG_TOOLBAR:

    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": "kitsune.settings.show_toolbar_callback"}

    INSTALLED_APPS = INSTALLED_APPS + ("debug_toolbar",)

    MIDDLEWARE = ("debug_toolbar.middleware.DebugToolbarMiddleware",) + MIDDLEWARE

# Set this to True to wrap each HTTP request in a transaction on this database.
ATOMIC_REQUESTS = config("ATOMIC_REQUESTS", default=True, cast=bool)

# CORS Setup
CORS_ALLOW_ALL_ORIGINS = True
CORS_URLS_REGEX = [
    r"^/api/1/gallery/.*$",
    r"^/api/1/kb/.*$",
    r"^/api/1/products/.*",
    r"^/api/1/users/get_token$",
    r"^/api/1/users/test_auth$",
    r"^/api/2/answer/.*$",
    r"^/api/2/pushnotification/.*$",
    r"^/api/2/notification/.*$",
    r"^/api/2/question/.*$",
    r"^/api/2/realtime/.*$",
    r"^/api/2/search/.*$",
    r"^/api/2/user/.*$",
    r"^/graphql/.*$",
]
# Now combine all those regexes with one big "or".
CORS_URLS_REGEX = re.compile("|".join("({0})".format(r) for r in CORS_URLS_REGEX))

# XXX Fix this when Bug 1059545 is fixed
CC_IGNORE_USERS = []

ACTSTREAM_SETTINGS = {
    "USE_JSONFIELD": True,
}

SILENCED_SYSTEM_CHECKS = [
    "fields.W340",  # null has no effect on ManyToManyField.
    "fields.W342",  # ForeignKey(unique=True) is usually better served by a OneToOneField
]

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())
ALLOWED_CIDR_NETS = config("ALLOWED_CIDR_NETS", default="", cast=Csv())
# in production set this to 'support.mozilla.org' and all other domains will redirect.
# can be a comma separated list of allowed domains.
# the first in the list will be the target of redirects.
# needs to be None if not set so that the middleware will
# be turned off. can't set default to None because of the Csv() cast.
ENFORCE_HOST = config("ENFORCE_HOST", default="", cast=Csv()) or None

# Allows you to specify waffle settings in the querystring.
WAFFLE_OVERRIDE = config("WAFFLE_OVERRIDE", default=DEBUG, cast=bool)

if config("SENTRY_DSN", None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    # see https://docs.sentry.io/learn/filtering/?platform=python
    def filter_exceptions(event, hint):
        # Ignore errors from specific loggers.
        if event.get("logger", "") == "django.security.DisallowedHost":
            return None

        return event

    sentry_sdk.init(
        dsn=config("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        release=config("GIT_SHA", default=None),
        server_name=PLATFORM_NAME,
        environment=config("SENTRY_ENVIRONMENT", default=""),
        before_send=filter_exceptions,
    )

# Dead Man Snitches
DMS_ENQUEUE_LAG_MONITOR_TASK = config("DMS_ENQUEUE_LAG_MONITOR_TASK", default=None)
DMS_SEND_WELCOME_EMAILS = config("DMS_SEND_WELCOME_EMAILS", default=None)
DMS_UPDATE_PRODUCT_DETAILS = config("DMS_UPDATE_PRODUCT_DETAILS", default=None)
DMS_GENERATE_MISSING_SHARE_LINKS = config("DMS_GENERATE_MISSING_SHARE_LINKS", default=None)
DMS_REBUILD_KB = config("DMS_REBUILD_KB", default=None)
DMS_UPDATE_TOP_CONTRIBUTORS = config("DMS_UPDATE_TOP_CONTRIBUTORS", default=None)
DMS_UPDATE_L10N_COVERAGE_METRICS = config("DMS_UPDATE_L10N_COVERAGE_METRICS", default=None)
# DMS_CALCULATE_CSAT_METRICS = config("DMS_CALCULATE_CSAT_METRICS", default=None)
DMS_REPORT_EMPLOYEE_ANSWERS = config("DMS_REPORT_EMPLOYEE_ANSWERS", default=None)
DMS_UPDATE_WEEKLY_VOTES = config("DMS_UPDATE_WEEKLY_VOTES", default=None)
DMS_UPDATE_SEARCH_CTR_METRIC = config("DMS_UPDATE_SEARCH_CTR_METRIC", default=None)
DMS_UPDATE_CONTRIBUTOR_METRICS = config("DMS_UPDATE_CONTRIBUTOR_METRICS", default=None)
DMS_AUTO_ARCHIVE_OLD_QUESTIONS = config("DMS_AUTO_ARCHIVE_OLD_QUESTIONS", default=None)
DMS_REINDEX = config("DMS_REINDEX", default=None)
DMS_REINDEX_ES = config("DMS_REINDEX_ES", default=None)
# DMS_PROCESS_EXIT_SURVEYS = config("DMS_PROCESS_EXIT_SURVEYS", default=None)
# DMS_SURVEY_RECENT_ASKERS = config("DMS_SURVEY_RECENT_ASKERS", default=None)
# DMS_UPDATE_VISITORS_METRIC = config('DMS_UPDATE_VISITORS_METRIC', default=None)
DMS_UPDATE_L10N_METRIC = config("DMS_UPDATE_L10N_METRIC", default=None)
DMS_RELOAD_WIKI_TRAFFIC_STATS = config("DMS_RELOAD_WIKI_TRAFFIC_STATS", default=None)
DMS_CACHE_MOST_UNHELPFUL_KB_ARTICLES = config("DMS_CACHE_MOST_UNHELPFUL_KB_ARTICLES", default=None)
DMS_RELOAD_QUESTION_TRAFFIC_STATS = config("DMS_RELOAD_QUESTION_TRAFFIC_STATS", default=None)
DMS_SEND_WEEKLY_READY_FOR_REVIEW_DIGEST = config(
    "DMS_SEND_WEEKLY_READY_FOR_REVIEW_DIGEST", default=None
)
DMS_FIX_CURRENT_REVISIONS = config("DMS_FIX_CURRENT_REVISIONS", default=None)
DMS_COHORT_ANALYSIS = config("DMS_COHORT_ANALYSIS", default=None)
DMS_UPDATE_L10N_CONTRIBUTOR_METRICS = config("DMS_UPDATE_L10N_CONTRIBUTOR_METRICS", default=None)

PROD_DETAILS_CACHE_NAME = "product-details"
PROD_DETAILS_STORAGE = config(
    "PROD_DETAILS_STORAGE", default="product_details.storage.PDDatabaseStorage"
)

DISABLE_HOSTNAME_MIDDLEWARE = config("DISABLE_HOSTNAME_MIDDLEWARE", default=False, cast=bool)

DISABLE_FEEDS = config("DISABLE_FEEDS", default=False, cast=bool)
DISABLE_QUESTIONS_LIST_GLOBAL = config("DISABLE_QUESTIONS_LIST_GLOBAL", default=False, cast=bool)
DISABLE_QUESTIONS_LIST_ALL = config("DISABLE_QUESTIONS_LIST_ALL", default=False, cast=bool)
IMAGE_ATTACHMENT_USER_LIMIT = config("IMAGE_ATTACHMENT_USER_LIMIT", default=50, cast=int)

# list of strings to match against user agent to block
USER_AGENT_FILTERS = config("USER_AGENT_FILTERS", default="", cast=Csv())

BADGE_LIMIT_L10N_KB = config("BADGE_LIMIT_L10N_KB", default=10, cast=int)
BADGE_LIMIT_SUPPORT_FORUM = config("BADGE_LIMIT_SUPPORT_FORUM", default=30, cast=int)
BADGE_MAX_RECENT = config("BADGE_MAX_RECENT", default=15, cast=int)
BADGE_PAGE_SIZE = config("BADGE_PAGE_SIZE", default=50, cast=int)

# The canonical, production URL without a trailing slash
CANONICAL_URL = "https://support.mozilla.org"

# Products to exclude from featured articles under
# wiki/utils.py
EXCLUDE_PRODUCT_SLUGS_FEATURED_ARTICLES = [
    "firefox-amazon-devices",
    "firefox-fire-tv",
    "focus-firefox",
    "thunderbird",
]

# Substring to match in slug in order to display the SUMO CTA banner
SUMO_BANNER_STRING = config("SUMO_BANNER_STRING", default="", cast=Csv())

# List of domains that links are allowed
ALLOW_LINKS_FROM = [
    "mozilla.org",
    "mozilla.com",
    "mozillafoundation.org",
    "getpocket.com",
    "thunderbird.net",
]

# Regexes
TOLL_FREE_REGEX = re.compile(r"^.*8(00|33|44|55|66|77|88)[2-9]\d{6,}$")
REGEX_TIMEOUT = config("REGEX_TIMEOUT", default=5, cast=int)
NANP_REGEX = re.compile(r"[0-9]{3}-?[a-zA-Z2-9][a-zA-Z0-9]{2}-?[a-zA-Z0-9]{4}")

if ES_ENABLE_CONSOLE_LOGGING and DEV:
    es_trace_logger = logging.getLogger("elasticsearch.trace")
    es_trace_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    es_trace_logger.addHandler(handler)

# Zendesk Section
ZENDESK_SUBDOMAIN = config("ZENDESK_SUBDOMAIN", default="")
ZENDESK_API_TOKEN = config("ZENDESK_API_TOKEN", default="")
ZENDESK_USER_EMAIL = config("ZENDESK_USER_EMAIL", default="")
ZENDESK_TICKET_FORM_ID = config("ZENDESK_TICKET_FORM_ID", default="360000417171", cast=int)
ZENDESK_PRODUCT_FIELD_ID = config("ZENDESK_PRODUCT_FIELD_ID", default="360047198211", cast=int)
ZENDESK_CATEGORY_FIELD_ID = config("ZENDESK_CATEGORY_FIELD_ID", default="360047206172", cast=int)
ZENDESK_OS_FIELD_ID = config("ZENDESK_OS_FIELD_ID", default="360018604871", cast=int)
ZENDESK_COUNTRY_FIELD_ID = config("ZENDESK_COUNTRY_FIELD_ID", default="360026463511", cast=int)

# Django CSP configuration
CSP_INCLUDE_NONCE_IN = ["script-src"]

CSP_DEFAULT_SRC = ("'none'",)

CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "https://*.mozilla.org",
    "https://*.itsre-sumo.mozilla.net",
    "https://*.webservices.mozgcp.net",
    "https://*.google-analytics.com",
    "https://*.googletagmanager.com",
    "https://pontoon.mozilla.org",
    "https://*.jsdelivr.net",
)

CSP_IMG_SRC = (
    "'self'",
    "data:",
    "https://*.mozaws.net",
    "https://*.itsre-sumo.mozilla.net",
    "https://*.webservices.mozgcp.net",
    "https://*.google-analytics.com",
    "https://profile.accounts.firefox.com",
    "https://firefoxusercontent.com",
    "https://secure.gravatar.com",
    "https://i1.wp.com",
    "https://mozillausercontent.com",
    "https://*.gravatar.com",
)

CSP_MEDIA_SRC = (
    "'self'",
    "https://*.itsre-sumo.mozilla.net",
    "https://*.webservices.mozgcp.net",
)

CSP_FRAME_SRC = (
    "'self'",
    "https://*.youtube.com",
)

CSP_FONT_SRC = (
    "'self'",
    "https://*.itsre-sumo.mozilla.net",
    "https://*.webservices.mozgcp.net",
)

CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://*.itsre-sumo.mozilla.net",
    "https://*.webservices.mozgcp.net",
    "https://*.jsdelivr.net",
)

CSP_FORM_ACTION = ("'self'",)

CSP_MANIFEST_SRC = (
    "https://support.allizom.org",
    "https://support.mozilla.org",
)

CSP_CONNECT_SRC = (
    "'self'",
    "https://*.google-analytics.com",
    "https://location.services.mozilla.com",
)

if DEBUG:
    CSP_STYLE_SRC += ("'unsafe-inline'",)
    CSP_SCRIPT_SRC += (
        "'unsafe-inline'",
        "'unsafe-eval'",
    )

# Trusted Contributor Groups
TRUSTED_GROUPS = [
    "Forum Moderators",
    "Administrators",
    "SUMO Locale Leaders",
    "Knowledge Base Reviewers",
    "Reviewers",
    # Temporary workaround to exempt individual users if needed
    "Escape Spam Filtering",
    "trusted contributors",
    "kb-contributors",
    "l10n-contributors",
    "forum-contributors",
    "social-contributors",
    "mobile-contributors",
]

# GraphQL configuration
GRAPHENE = {
    "SCHEMA": "kitsune.schema.schema",
}

# Contributor Groups
LEGACY_CONTRIBUTOR_GROUPS = [
    "Contributors",
    "Registered as contributor",
    "trusted contributors",
]

# Wagtail configuration
WAGTAIL_SITE_NAME = "Mozilla Support"
WAGTAILADMIN_BASE_URL = config("WAGTAILADMIN_BASE_URL", default="https://support.mozilla.org")

WAGTAIL_I18N_ENABLED = True
