# encoding: utf-8

# Database
{% if target == 'production' %}
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
{% if target == 'development' %}
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
{% endif %}

# Debug
{% if target == 'development' %}
DEBUG = True
TEMPLATE_DEBUG = True
{% endif %}
