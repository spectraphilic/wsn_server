# Django
from django.urls import re_path

# Import from boot
from . import views


urlpatterns = [
    re_path(r'^sendfile/(?P<path>.*)$', views.SendfileView.as_view(), name='sendfile'),
]
