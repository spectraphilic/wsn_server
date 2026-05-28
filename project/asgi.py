"""
ASGI config for project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

application = get_asgi_application()


# WebSockets support requires Django channels
from django.conf import settings # noqa: E402
if 'channels' in settings.INSTALLED_APPS:
    from channels.auth import AuthMiddlewareStack
    from channels.routing import ProtocolTypeRouter, URLRouter
    from .urls_ws import urlpatterns

    router = URLRouter(urlpatterns)

    application = ProtocolTypeRouter({
        'http': application,
        'websocket': AuthMiddlewareStack(router),
    })
