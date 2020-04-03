import logging
import logging.config

from django.conf import settings


config = {
    'version': 1,
    'disable_existing_loggers': True,
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
            'level': logging.DEBUG,
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
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
            'handlers': ['console'],
            'propogate': True,
            'level': settings.LOG_LEVEL,
        },
        'k.lib.email': {
            'handlers': ['console'],
            'propogate': True,
            'level': logging.DEBUG,
        },
        'k.users.views': {
            'handlers': ['console'],
            'propogate': True,
            'level': logging.DEBUG,
        },
        'django.request': {
            'handlers': ['console'],
            'propogate': True,
            'level': settings.LOG_LEVEL,
        },
    },
}

logging.config.dictConfig(config)
logging.captureWarnings(True)
