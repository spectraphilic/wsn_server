# Django
from django.urls import path

# Import from boot
from . import views


urlpatterns = [
    path('sendfile/<path>', views.SendfileView.as_view(), name='sendfile'),
]
