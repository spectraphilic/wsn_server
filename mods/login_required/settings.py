# ruff: noqa: F821

insert(
    MIDDLEWARE,
    'django.contrib.auth.middleware.LoginRequiredMiddleware',
    after='django.contrib.auth.middleware.AuthenticationMiddleware',
)
