import logging

from django.conf import settings
from django.utils.log import dictConfig


config = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': logging.ERROR,
        'handlers': ['sentry'],
    },
    'formatters': {
        'default': {
            'format': '{0}: %(asctime)s %(name)s:%(levelname)s %(message)s: '
                      '%(pathname)s:%(lineno)s'.format(settings.SYSLOG_TAG),
        }
    },
    'handlers': {
        'syslog': {
            'class': 'logging.handlers.SysLogHandler',
            'formatter': 'default',
            'facility': logging.handlers.SysLogHandler.LOG_LOCAL7,
            'level': settings.LOG_LEVEL,
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': logging.ERROR,
        },
        'sentry': {
            'class': 'raven.contrib.django.handlers.SentryHandler',
            'level': logging.ERROR,
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'level': settings.LOG_LEVEL,
        },
    },
    'loggers': {
        'k': {
            'handlers': ['syslog'],
            'propogate': True,
            # Use the most permissive setting. It is filtered in the handlers.
            'level': logging.DEBUG,
        },
        'django.request': {
            'handlers': ['syslog'],
            'propogate': True,
            # Use the most permissive setting. It is filtered in the handlers.
            'level': logging.DEBUG,
        },
        'raven': {
            'level': logging.ERROR,
            'handlers': ['syslog', 'mail_admins'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': logging.ERROR,
            'handlers': ['syslog', 'mail_admins'],
            'propagate': False,
        },
    },
}

if settings.DEBUG:
    config['formatters']['default']['datefmt'] = '%H:%M:%S'
    config['loggers']['k']['handlers'] = ['console']
    config['loggers']['django.request']['handlers'] = ['console']
    config['root']['handlers'] = ['console']
else:
    from celery import current_app
    from celery.utils.log import LoggingProxy

    task_log = logging.getLogger('k.celery')
    task_proxy = LoggingProxy(task_log)
    current_app.conf.update(
        CELERYD_LOG_FILE = task_proxy,
        CELERYD_LOG_COLOR = False
    )

dictConfig(config)
