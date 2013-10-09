# The test system uses this to override settings in settings.py and
# settings_local.py with settings appropriate for testing.
import os

ES_LIVE_INDEXING = False
ES_INDEX_PREFIX = 'sumotest'
ES_INDEXES = {'default': 'test'}
ES_WRITE_INDEXES = ES_INDEXES

# Make sure Celery is EAGER.
CELERY_ALWAYS_EAGER = True

# Make sure we use port 6383 db 2 redis for tests.  That's db 2 of the
# redis test config.  That shouldn't collide with anything else.
REDIS_BACKENDS = {
    'default': 'redis://localhost:6383?socket_timeout=0.5&db=2',
    'karma': 'redis://localhost:6383?socket_timeout=0.5&db=2',
    'helpfulvotes': 'redis://localhost:6383?socket_timeout=0.5&db=2',
}

# Some cron jobs are skipped on stage.
STAGE = False

SESSION_COOKIE_SECURE = False

# The way we do live server test cases is greedy with ports. This gives
# it more ports, but won't clobber settings from the environment.
if 'DJANGO_LIVE_TEST_SERVER_ADDRESS' not in os.environ:
    os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8081-8090'

# This quells south's crazy debug logging
import logging
import south.logger
logging.getLogger('south').setLevel(logging.INFO)
