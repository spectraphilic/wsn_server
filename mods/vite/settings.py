INSTALLED_APPS.append('django_vite')

DJANGO_VITE = {
    'default': {
        'dev_mode': DEBUG,
    },
}

if not DEBUG:
    STATICFILES_DIRS.append(BASE_DIR / 'var' / 'build')
