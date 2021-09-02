# Standard Library
import time

# Django
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# App
from wsn import tasks


#
# 4G
#
@method_decorator(csrf_exempt, name='dispatch')
class MeshliumView(View):
    """
    Create frames sent through 4G by the waspmotes.

    To make it simple in the motes sketch, we use the same method as
    implemented in the Meshlium.
    """

    def post(self, request, *args, **kwargs):
        # Payload
        payload = request.POST.get('frame')
        if type(payload) is str:
            payload = [payload]

        # Envelop
        envelop = {
            'payload': payload,
            'received': int(time.time()),
        }
        remote_addr = request.META.get('REMOTE_ADDR', '')
        if remote_addr:
            envelop['remote_addr'] = remote_addr

        # Send tasks to workers
        tasks.in_meshlium.delay(envelop)
        tasks.archive.delay('meshlium', envelop)

        # Ok
        return HttpResponse(status=200)


#
# Iridium
#
@method_decorator(csrf_exempt, name='dispatch')
class IridiumView(View):

    def post(self, request, *args, **kwargs):
        # Payload
        payload = dict(request.POST)

        # Envelop
        envelop = {
            'payload': payload,
            'received': int(time.time()),
        }
        remote_addr = request.META.get('REMOTE_ADDR', '')
        if remote_addr:
            envelop['remote_addr'] = remote_addr

        # Send tasks to workers
        tasks.in_iridium.delay(envelop)
        tasks.archive.delay('iridium', envelop)

        # Ok
        return HttpResponse(status=200)
