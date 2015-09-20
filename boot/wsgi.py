"""
The purpose of this module is to wrap the wsgi application to add these
features:

  /ping  -- URL used for monitoring purposes, to know whether the application
            is responding or not.

"""

from project.wsgi import application


class PingMiddleware:

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'] == '/ping':
            # we're being asked to render the profile view
            text = 'pong'.encode('utf-8')
            start_response('200 OK', [
                ('Content-type', 'text/plain; charset="utf-8"'),
                ('Content-length', str(len(text)))])
            return [text]

        return self.app(environ, start_response)

# Add url /ping for monitoring
application = PingMiddleware(application)
