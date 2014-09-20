
class PingMiddleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'] == '/ping':
            # we're being asked to render the profile view
            text = 'pong'
            start_response('200 OK', [
                ('content-type', 'text/html; charset="UTF-8"'),
                ('content-length', str(len(text)))])
            return [text]

        return self.app(environ, start_response)
