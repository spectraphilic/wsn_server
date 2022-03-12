# Django
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView


User = get_user_model()

class SvelteBaseView(TemplateView):
    template_name = 'demo/svelte_page.html'

    page_app = None # Name of Svelte app in src/main.js
    page_title = None

    # Props to initialize the Svelte app
    def props(self):
        return {}

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


class UsersCreateView(SvelteBaseView):
    page_app = 'UsersCreate'
    page_title = 'Create user'
