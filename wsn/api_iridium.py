# Django
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# App
from . import tasks


@method_decorator(csrf_exempt, name='dispatch')
class IridiumView(View):

    def post(self, request, *args, **kwargs):
        POST = dict(request.POST)
        tasks.in_iridium.delay(POST)
        return HttpResponse(status=200)
