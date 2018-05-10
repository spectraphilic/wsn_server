# Import from the Standard Library
import os

# Import from Django
from django.conf import settings
from django.http import Http404
from django.views.generic import View

# Import ..
from sendfile import sendfile


class SendfileView(View):

    def get(self, request, **kwargs):
        if request.user.is_anonymous:
            raise Http404

        path = kwargs['path']
        path = os.path.join(settings.SENDFILE_ROOT, path)
        path = os.path.abspath(path)
        return sendfile(request, path)
