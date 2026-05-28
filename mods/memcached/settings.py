CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': 'unix:/run/memcached/memcached.sock',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
