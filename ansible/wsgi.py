"""
The purpose of this module is to wrap the wsgi application to add these
features:

  /ping  -- URL used for monitoring purposes, to know whether the application
            is responding or not.

"""

from project.wsgi import application


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


# Add url /ping for monitoring
application = ping_middleware(application)
