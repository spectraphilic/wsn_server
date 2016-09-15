# Import from Django
from django.conf.urls import url

# Import from boot
from .views import SendfileView


urlpatterns = [
    url(r'^sendfile/$', SendfileView.as_view(), name='sendfile'),
]
