# Standard Library
import base64
from datetime import datetime, time

import pytz

# Django
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# App
from .models import Frame, frame_to_database
from .parsers import waspmote


oslo = pytz.timezone('Europe/Oslo')
def epoch_to_oslo(epoch):
    """
    Convert Unixe epoch time to local Europe/Oslo time.
    """
    dt = datetime.utcfromtimestamp(epoch)
    dt = datetime.utcfromtimestamp(epoch).replace(tzinfo=pytz.utc)
    return dt.astimezone(oslo)


def postfix(frame, save=False, verbose=False):
    """
    Returns None if there's nothing to fix.
    Returns True if the frame has been fixed, False if it has not.
    """
    name = 'sw-002'
    if frame.metadata.name != name:
        return None

    # The bad data goes from 00:10 to 02:00 local time
    # Or from 00:05 to 01:00 (from March 14 to March 20)
    dt = epoch_to_oslo(frame.time)
    if time(0) < dt.time() <= time(2):
        # Find out the time distance from the previous frame
        frames = Frame.objects.filter(metadata__name=name).order_by('id')
        prev = frames.filter(pk__lt=frame.pk).last()
        diff = frame.time - prev.time

        # The clock jumps +1 day, so the time difference between the 2
        # consecutive frames is greather than 1 day. We add a margin
        # error of 2h for the upper limit, so we don't catch too much.
        one_hour = 3600
        one_day = 24 * 3600
        if one_day < diff < one_day + one_hour * 2:
            old_time = frame.time
            new_time = old_time - one_day
            if verbose:
                old_dt = datetime.utcfromtimestamp(old_time)
                new_dt = datetime.utcfromtimestamp(new_time)
                print(f'Fix {frame.pk} {old_dt} -> {new_dt}')

            if save:
                frame.time = new_time
                frame.save()
                return True

    return False


@method_decorator(csrf_exempt, name='dispatch')
class MeshliumView(View):
    """
    Create frames sent through 4G by the waspmotes
    """

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
                metadata, objs = frame_to_database(validated_data)

                # Fix time in sw-002
#               for obj in objs:
#                   postfix(obj, save=True, verbose=False)

        return HttpResponse(status=200)
