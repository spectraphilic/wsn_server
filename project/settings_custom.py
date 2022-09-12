"""
Put your custom settings here, not in settings.py

Settings structure:

- settings.py         : Defaults from Django, do not edit
- settings_ansible.py : Generated by Ansible (not committed)
- settings_custom.py  : Your custom project settings, edit this one
"""

# Standard Library
import os
from socket import getfqdn

# Requirements
from dotenv import load_dotenv

# Project
from project.settings_ansible import *


# Load environment variables
load_dotenv(f'{BASE_DIR}/.envrc')

# Applications
def replace(l, a, b):
    return [b if x == a else x for x in l]

INSTALLED_APPS += [
    # Requirements
    'django_vite',
    'strawberry.django',
    # Project apps
    'apps.boot',
    # Requirements
    'drf_spectacular',
    'rangefilter',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_api_key',
    # Project
    'api',
    'qc',
    'wsn',
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'wsn': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}

# Static files
STATICFILES_DIRS = [
    #BASE_DIR / 'project' / 'static',
]

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'project' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Emails
ADMINS = (
    ('J. David Ibanez', 'jdavid.ibp@gmail.com'),
)
MANAGERS = ADMINS

fqdn = getfqdn()
DEFAULT_FROM_EMAIL = 'webmaster@' + fqdn
SERVER_EMAIL = 'root@' + fqdn

# Vite
DJANGO_VITE_DEV_SERVER_PORT = 5173
DJANGO_VITE_ASSETS_PATH = BASE_DIR / 'var' / 'build'
DJANGO_VITE_DEV_MODE = DEBUG
if not DJANGO_VITE_DEV_MODE:
    STATICFILES_DIRS.append(DJANGO_VITE_ASSETS_PATH)

# If not defined the producer will hang forever when the broker is not
# available. Iridium requires the callback to run in less than 3s.
# https://github.com/celery/celery/issues/4296#issuecomment-444104961
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'interval_start': 0,  # Retry immediately (1st retry)
    'interval_step': 0.5, # Add .5s to every subsequent retry
    'interval_max': 3,    # Max 3s
    'max_retries': 3,     # 0 + 0.5 + 1 = 1.5s
}

# To be extra sure the messages are not handled by a worker from another
# project: do not use the default 'celery' queue.
CELERY_TASK_ROUTES = {
    '*': {'queue': 'celery_wsn'},
}

# Task options (not standard)
CELERY_TASK_MAX_RETRIES = None # Retry forever

# Celery Once: use the file backend, to avoid adding another service (Redis)
CELERY_ONCE = {
    'backend': 'celery_once.backends.File',
    'settings': {
        #'location': '/tmp/celery_once',
        #'default_timeout': 60 * 60
    }
}

CLICKHOUSE_HOST = 'localhost'
CLICKHOUSE_USER = 'default'
CLICKHOUSE_PASSWORD = ''
CLICKHOUSE_NAME = 'wsn'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication', # For the browsable views
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAdminUser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'PAGE_SIZE': 100,
    'STRICT_JSON': False,
}

# wsn: folder where frames are archived
WSN_DATA_DIR = BASE_DIR / 'var' / 'data'
WSN_CIPHER_KEY = os.environ.get('WSN_CIPHER_KEY', None)
