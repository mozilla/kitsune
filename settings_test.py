# The test system uses this to override settings in settings.py and
# settings_local.py with settings appropriate for testing.

# Make sure Celery is EAGER.
CELERY_ALWAYS_EAGER = True

# Make sure we use port 6383 db 2 redis for tests.  That's db 2 of the
# redis test config.  That shouldn't collide with anything else.
REDIS_BACKENDS = {
    'default': 'redis://localhost:6383?socket_timeout=0.5&db=2',
    'karma': 'redis://localhost:6383?socket_timeout=0.5&db=2',
    'helpfulvotes': 'redis://localhost:6383?socket_timeout=0.5&db=2',
}
