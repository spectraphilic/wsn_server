DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '{{ postgres.name }}',
        'USER': '{{ postgres.user }}',
        'PASSWORD': '{{ postgres.password }}',
        'HOST': '{{ postgres.host|default() }}',
        'PORT': '',
    }
}
