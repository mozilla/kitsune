from django.conf import settings
# The test system uses this to override settings in settings.py and
# settings_local.py with settings appropriate for testing.

# Make sure Celery is EAGER.
CELERY_ALWAYS_EAGER = True

# Make sure the doctypes (the keys) match the doctypes in ES_INDEXES
# in settings.py and settings_local.py.
ES_INDEXES = {'default': 'sumo_test' + settings.ES_INDEX_PREFIX}
ES_WRITE_INDEXES = ES_INDEXES

print ES_INDEXES

# This makes sure we only turn on ES stuff when we're testing ES
# stuff.
ES_LIVE_INDEXING = False

# Make sure we use port 6383 db 2 redis for tests.  That's db 2 of the
# redis test config.  That shouldn't collide with anything else.
REDIS_BACKENDS = {
    'default': 'redis://localhost:6383?socket_timeout=0.5&db=2',
    'karma': 'redis://localhost:6383?socket_timeout=0.5&db=2',
    'helpfulvotes': 'redis://localhost:6383?socket_timeout=0.5&db=2',
}

# Use fake webtrends settings.
WEBTRENDS_PROFILE_ID = 'ABC123'
