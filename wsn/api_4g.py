# Standard Library
import base64

# Django
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# App
from .models import frame_to_database
from .parsers import waspmote


#
# Create frames sent through 4G by the waspmotes
#

@method_decorator(csrf_exempt, name='dispatch')
class MeshliumView(View):

    def post(self, request, *args, **kwargs):
        datas = request.POST.get('frame')
        if type(datas) is str:
            datas = [datas]

        for data in datas:
            # Parse frame
            data = base64.b16decode(data)
            while data:
                frame, data = waspmote.parse_frame(data)
                if frame is None:
                    break

                validated_data = waspmote.data_to_json(frame)

                # Add remote addr to tags
                remote_addr = request.META.get('REMOTE_ADDR', '')
                validated_data['tags']['remote_addr'] = remote_addr

                # Save to database
                frame_to_database(validated_data)

        return HttpResponse(status=200)
