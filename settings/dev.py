# Inherit from base settings
from .base import *  # pylint:disable=W0614,W0401

ALLOWED_HOSTS = ['127.0.0.1']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'apps_info': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/apps_info.log',
            'formatter': 'simple',
        },
        'apps_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/apps_debug.log',
            'formatter': 'simple',
        },
        'trace': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/trace.log',
            'formatter': 'simple',
            'maxBytes': 1000000,
            'backupCount': 2,
        },
        'events': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/events.log',
            'formatter': 'simple',
        },
        'errors': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'logs/errors.log',
            'formatter': 'simple',
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(name)s [%(levelname)s] %(message)s'
        }
    },
    'loggers': {
        '': {
            'handlers': ['trace', 'errors'],
            'propagate': True,
        },
        'idm': {
            'handlers': ['apps_debug', 'apps_info', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
