# Standard Library
#import base64

# Django
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# App
from .models import frame_to_database
from .parsers import waspmote


@method_decorator(csrf_exempt, name='dispatch')
class IridiumView(View):

    def post(self, request, *args, **kwargs):
        POST = request.POST
        imei = POST['imei'] # 300234010753370
        momsn = POST['momsn'] # 12345
        transmit_time = POST['transmit_time'] # 12-10-10 10:41:50
        iridium_latitude = POST['iridium_latitude'] # 52.3867
        iridium_longitude = POST['iridium_longitude'] # 0.2938
        iridium_cep = POST['iridium_cep'] # 8
        data = POST['data'] # 48656c6c6f20576f726c6420526f636b424c4f434b


        frame, data = waspmote.parse_frame(data)
        if frame is None:
            return HttpResponse(status=400)

        validated_data = waspmote.data_to_json(frame)

        # Add metadata
        tags = validated_data['tags']
        tags['imei'] = imei

        # Add data
        frame = validated_data['frames'][0]
        frame['momsn'] = momsn # This is a lot like motes 'frame' but uses 2 bytes
        frame['received'] = transmit_time # FIXME Convert to epoch
        frame['iridium_latitude'] = iridium_latitude
        frame['iridium_longitude'] = iridium_longitude
        frame['iridium_cep'] = iridium_cep

        # Save to database
        frame_to_database(validated_data)
        return HttpResponse(status=200)
