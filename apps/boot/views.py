# Standard Library
import os

# Django
from django.conf import settings
from django.http import Http404
from django.views.generic import TemplateView, View

# Requirements
from django_sendfile import sendfile


class SendfileView(View):

    def get(self, request, **kwargs):
        if request.user.is_anonymous:
            raise Http404

        path = kwargs['path']
        path = os.path.join(settings.SENDFILE_ROOT, path)
        path = os.path.abspath(path)
        return sendfile(request, path)


class SvelteBaseView(TemplateView):
    template_name = 'boot/svelte_page.html'

    # Name of Svelte app in src/main.js
    page_app = None

    # Props to initialize the Svelte app
    def props(self):
        return {}


class SvelteHelloView(SvelteBaseView):
    """
    Example of a Svelte view.
    """

    page_app = 'Hello'
    def props(self):
        name = self.kwargs['name']
        return {
            'name': name,
        }
