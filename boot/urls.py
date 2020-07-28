# Django
from django.conf.urls import url
from django.urls import path

# Import from boot
from . import views


urlpatterns = [
    path('sendfile/<path>', views.SendfileView.as_view(), name='sendfile'),
    path('svelte/hello/<name>', views.SvelteHelloView.as_view()),
]
