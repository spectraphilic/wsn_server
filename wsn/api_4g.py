# Standard Library
import time

# Django
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# App
from . import tasks


@method_decorator(csrf_exempt, name='dispatch')
class MeshliumView(View):
    """
    Create frames sent through 4G by the waspmotes
    """

    def post(self, request, *args, **kwargs):
        datas = request.POST.get('frame')
        if type(datas) is str:
            datas = [datas]

        # Received
        kw = {}
        kw['received'] = int(time.time())

        # Remote address
        remote_addr = request.META.get('REMOTE_ADDR', '')
        if remote_addr:
            kw['remote_addr'] = remote_addr

        # Send task to worker
        tasks.in_4G.delay(datas, **kw)

        return HttpResponse(status=200)
