"""
WSGI config for project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

application = get_wsgi_application()

# Add url /ping for monitoring
def ping_middleware(app):
    def ping(environ, start_response, app=app):
        if environ['PATH_INFO'] == '/ping':
            text = 'pong'.encode('utf-8')
            start_response('200 OK', [
                ('Content-type', 'text/plain; charset="utf-8"'),
                ('Content-length', str(len(text)))])
            return [text]

        return app(environ, start_response)

    return ping

application = ping_middleware(application)
