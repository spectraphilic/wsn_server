from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.urls import path


@login_not_required
def ping(request):
    return HttpResponse('pong', content_type='text/plain')

urlpatterns = [
    path('ping', ping), # Do not remove
]
