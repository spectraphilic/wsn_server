# encoding: utf-8

from project.settings import *

# Database
{% if django_database == 'postgres' %}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',               # Set to empty string for localhost.
        'PORT': '',               # Set to empty string for default.
    }
}
{% endif %}

# Email
{% if django_debug %}
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
{% endif %}

# Debug
DEBUG = {{ django_debug }}
TEMPLATE_DEBUG = {{ django_debug }}

# Security
ALLOWED_HOSTS = ["{{ django_domain }}"]
