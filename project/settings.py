"""
Django settings for project project.

Generated by 'django-admin startproject' using Django 2.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Requirements
    'rangefilter',
    'rest_framework',
    'rest_framework.authtoken',
    # Project
    'api.apps.ApiConfig',
    'qc.apps.QCConfig',
    'wsn.apps.WsnConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC' # XXX

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'

#
# Emails
#
from socket import getfqdn

ADMINS = (
  ('J. David Ibanez', 'jdavid.ibp@gmail.com'),
)
MANAGERS = ADMINS

fqdn = getfqdn()
DEFAULT_FROM_EMAIL = 'webmaster@' + fqdn
SERVER_EMAIL = 'root@' + fqdn

#
# Logging
#

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

#
# Security related
#

LOGIN_URL = '/admin/login/'

#
# API
#

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAdminUser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication', # For the browsable views
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
    #'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'STRICT_JSON': False,
}

#
# ClickHouse
#

CLICKHOUSE_HOST = 'localhost'
CLICKHOUSE_USER = 'default'
CLICKHOUSE_PASSWORD = ''
CLICKHOUSE_NAME = 'wsn'


#
# Celery
#

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

# wsn: folder where frames are archived
DATA_DIR = os.path.join(BASE_DIR, 'var', 'data')
