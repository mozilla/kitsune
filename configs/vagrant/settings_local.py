from kitsune.settings import *
import sys

INSTALLED_APPS = list(INSTALLED_APPS)
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)

TESTING = 'test' in sys.argv

DEBUG = True
TEMPLATE_DEBUG = DEBUG
SESSION_COOKIE_SECURE = False

# Allows you to run Kitsune without running Celery---all tasks
# will be done synchronously.
CELERY_ALWAYS_EAGER = True

# Allows you to specify waffle settings in the querystring.
WAFFLE_OVERRIDE = True

# Change this to True if you're going to be doing search-related
# work.
ES_LIVE_INDEXING = False

# Basic cache configuration for development.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'localhost:11211',
        'PREFIX': 'sumo:',
    }
}

DATABASES = {
    'default': {
        'NAME': 'kitsune',
        # 'NAME': 'kitsune_generatedata',
        'ENGINE': 'django.db.backends.mysql',
        # 'HOST': 'mariadb',
        'HOST': 'localhost',
        'USER': 'root',
        'PASSWORD': 'rootpass',
        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
        'TEST_CHARSET': 'utf8',
        'TEST_COLLATION': 'utf8_unicode_ci',
    },
}

REDIS_BACKENDS = {
    'default': 'redis://localhost:6383?socket_timeout=0.5&db=0',
    'helpfulvotes': 'redis://localhost:6383?socket_timeout=0.5&db=2',
}

LESS_PREPROCESS = True
LESS_BIN = path('node_modules/.bin/lessc')
UGLIFY_BIN = path('node_modules/.bin/uglifyjs')
CLEANCSS_BIN = path('node_modules/.bin/cleancss')
NUNJUCKS_PRECOMPILE_BIN = path('node_modules/.bin/nunjucks-precompile')

AXES_BEHIND_REVERSE_PROXY = False


# if not TESTING:
#     # debug_toolbar breaks the tests.
#     INSTALLED_APPS += ['debug_toolbar']
#     MIDDLEWARE_CLASSES += ['debug_toolbar.middleware.DebugToolbarMiddleware']

#     class ContainsEverything(object):
#         def __contains__(self, item):
#             return True

#     INTERNAL_IPS = ContainsEverything()

#     DEBUG_TOOLBAR_CONFIG = {
#         'SHOW_COLLAPSED': True,
#     }
