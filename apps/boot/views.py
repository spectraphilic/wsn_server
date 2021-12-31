# Standard Library
import os

# Django
from django.conf import settings
from django.contrib.auth import get_user_model
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

    page_app = None # Name of Svelte app in src/main.js
    page_title = None

    # Props to initialize the Svelte app
    def props(self):
        return {}


User = get_user_model()

class UsersListView(SvelteBaseView):
    page_app = 'UsersList'
    page_title = 'List of users'

class UsersUpdateView(SvelteBaseView):
    page_app = 'UsersUpdate'
    page_title = 'Update user'

    def props(self):
        pk = self.kwargs['id']
        user = User.objects.get(pk=pk)
        return {
            'id': pk,
            'username': user.username,
            'email': user.email,
            'firstName': user.first_name,
            'lastName': user.last_name,
        }
