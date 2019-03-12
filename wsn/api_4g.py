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
        frames = request.POST.get('frame')
        if type(frames) is str:
            frames = [frames]

        for frame in frames:
            # Parse frame
            frame = base64.b16decode(frame)
            frame, _ = waspmote.parse_frame(frame)
            validated_data = waspmote.data_to_json(frame)

            # Add remote addr to tags
            remote_addr = request.META.get('REMOTE_ADDR', '')
            validated_data['tags']['remote_addr'] = remote_addr

            # Save to database
            frame_to_database(validated_data)

        return HttpResponse(status=200)
