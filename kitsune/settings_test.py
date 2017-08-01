# The test system uses this to override settings in settings.py and
# settings_local.py with settings appropriate for testing.
import os

from decouple import config

ES_LIVE_INDEXING = False
ES_INDEX_PREFIX = 'sumotest'
ES_INDEXES = {
    'default': 'test-default',
    'non-critical': 'test-non-critical',
    'metrics': 'test-metrics',
}
ES_WRITE_INDEXES = ES_INDEXES

# Make sure Celery is EAGER.
CELERY_ALWAYS_EAGER = True
REDIS_URL = config('REDIS_URL', default='localhost')

# Make sure we use db 2 redis for tests.  That's db 2 of the
# redis test config.  That shouldn't collide with anything else.
REDIS_BACKENDS = {
    'default': '{}?socket_timeout=0.5&db=2'.format(REDIS_URL),
    'karma': '{}?socket_timeout=0.5&db=2'.format(REDIS_URL),
    'helpfulvotes': '{}?socket_timeout=0.5&db=2'.format(REDIS_URL),
}

# Some cron jobs are skipped on stage.
STAGE = False

SESSION_COOKIE_SECURE = False

# The way we do live server test cases is greedy with ports. This gives
# it more ports, but won't clobber settings from the environment.
if 'DJANGO_LIVE_TEST_SERVER_ADDRESS' not in os.environ:
    os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8081-8090'

# Tells django-axes we aren't behind a reverse proxy.
AXES_BEHIND_REVERSE_PROXY = False

# Make sure pipeline is enabled so it does not collectstatic on every test
PIPELINE_ENABLED = True
