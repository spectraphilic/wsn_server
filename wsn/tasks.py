# Standard Library
import base64
import codecs
import datetime
import json
import os

import pytz

# Celery
from celery import shared_task
from celery.utils.log import get_task_logger
from celery_once import QueueOnce

# Django
from django.conf import settings

# App
from .models import Frame, frame_to_database
from .parsers import waspmote


logger = get_task_logger(__name__)


#
# Archive
#
@shared_task(
    acks_late=True,             # Send ack at the end, not the beginning
    autoretry_for=(Exception,), # Retry for any exception
    max_retries=settings.CELERY_TASK_MAX_RETRIES,
    default_retry_delay=300,    # Retry after 5min (default is 3 minutes)
    # Run only one at a time
    base=QueueOnce,
    once={
        'keys': ['entry_name'],
        'timeout': 60,
    },
)
def archive(entry_name, envelop):
    """
    Save the frames to the filesystem.

    Parameters:

    - entry_name: name of the entry point (4G, Iridium, ..)
    - envelop: the data to save

    The envelop must be a dictionary with at least two keys: the 'payload', and
    the epoch time the data was 'received' by the server.

    The content of the payload depends on the entry point. The received time
    is used to decide the filepath where to save the envelop.

    The entry name is important because the format of the payload depends on
    it.
    """
    assert type(envelop) is dict
    assert 'payload' in envelop
    assert 'received' in envelop

    # File path where the file will be saved
    dt = datetime.datetime.utcfromtimestamp(envelop['received'])
    filepath = os.path.join(
        settings.DATA_DIR,
        entry_name,
        str(dt.year),
        dt.strftime('%Y%m%d')
    )

    # Create parent directory
    dirpath = os.path.dirname(filepath)
    os.makedirs(dirpath, exist_ok=True)

    # Append
    with open(filepath, 'a+') as f:
        f.write(json.dumps(envelop) + '\n')


#
# 4G
#
oslo = pytz.timezone('Europe/Oslo')
def epoch_to_oslo(epoch):
    """
    Convert Unixe epoch time to local Europe/Oslo time.
    """
    dt = datetime.datetime.utcfromtimestamp(epoch)
    dt = datetime.datetime.utcfromtimestamp(epoch).replace(tzinfo=pytz.utc)
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
    if datetime.time(0) < dt.time() <= datetime.time(2):
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
                old_dt = datetime.datetime.utcfromtimestamp(old_time)
                new_dt = datetime.datetime.utcfromtimestamp(new_time)
                print(f'Fix {frame.pk} {old_dt} -> {new_dt}')

            if save:
                frame.time = new_time
                frame.save()
                return True

    return False


@shared_task(
    acks_late=True,             # Send ack at the end, not the beginning
    autoretry_for=(Exception,), # Retry for any exception
    max_retries=settings.CELERY_TASK_MAX_RETRIES,
    default_retry_delay=300,    # Retry after 5min (default is 3 minutes)
)
def in_meshlium(envelop):
    # Pop the payload, what is left is metadata that we'll add later to the
    # frames
    payload = envelop.pop('payload')
    assert type(payload) is list

    for data in payload:
        # Parse frame
        data = base64.b16decode(data)
        while data:
            frame, data = waspmote.parse_frame(data)
            if frame is None:
                break

            # Add received time and remote address
            frame.update(envelop)

            # Save to database
            validated_data = waspmote.data_to_json(frame)
            metadata, objs = frame_to_database(validated_data)

            # Fix time in sw-002
            for obj in objs:
                postfix(obj, save=True, verbose=False)


#
# Iridium
#
@shared_task(
    acks_late=True,             # Send ack at the end, not the beginning
    autoretry_for=(Exception,), # Retry for any exception
    max_retries=settings.CELERY_TASK_MAX_RETRIES,
    default_retry_delay=300,    # Retry after 5min (default is 3 minutes)
)
def in_iridium(envelop):
    """
    Content of the payload (real example):
    {
      'device_type': ['ROCKBLOCK'],
      'serial': ['10003'],
      'momsn': ['694'],
      'transmit_time': ['19-03-23 10:30:29'],
      'imei': ['300234063769210'],
      'iridium_latitude': ['49.7932'],
      'iridium_longitude': ['142.5998'],
      'iridium_cep': ['98.0'],
      'data': ['48656c6c6f21205468697320697320612074657374206d6573736167652066726f6d20526f636b424c4f434b21']
    }
    """

    # Pop the payload, what is left is metadata. Now we discard this metadata,
    # but in the future we may add it to the frames.
    payload = envelop.pop('payload')
    assert type(payload) is dict

    def get(name, t):
        value = payload[name]
        assert type(value) is list and len(value) == 1
        return t(value[0])

    device_type = get('device_type', str) # ROCKBLOCK
    serial = get('serial', int ) # 10003
    momsn = get('momsn', int) # 694
    transmit_time = get('transmit_time', str) # 19-03-23 10:30:29
    imei = get('imei', int) # 300234063769210
    iridium_latitude = get('iridium_latitude', float) # 49.7932
    iridium_longitude = get('iridium_longitude', float) # 142.5998
    iridium_cep = get('iridium_cep', float) # 98.0
    data = get('data', str) # 48656c6c6f20576f726c6420526f636b424c4f434b

    # Convert
    data = codecs.decode(data, 'hex')
    transmit_time = datetime.datetime.strptime(transmit_time, '%y-%m-%d %H:%M:%S')
    transmit_time = int(transmit_time.timestamp())

    # Ignore test messages
    # TODO move test to waspmote.is_frame
    if not data.startswith(b'<=>'):
        logger.info(f'Ignore not-a-frame message "{data.decode()}')
        return

    # Parse data
    n = 0
    while data:
        frame, data = waspmote.parse_frame(data)
        if frame is None:
            raise ValueError(f'error parsing frame: {data}')

        validated_data = waspmote.data_to_json(frame)

        # Add metadata
        tags = validated_data['tags']
        tags['device_type'] = device_type
        tags['imei'] = imei
        tags['serial'] = serial

        # Add data
        frame = validated_data['frames'][0]['data']
        frame['momsn'] = momsn # This is a lot like motes 'frame' but uses 2 bytes
        frame['received'] = transmit_time
        frame['iridium_latitude'] = iridium_latitude
        frame['iridium_longitude'] = iridium_longitude
        frame['iridium_cep'] = iridium_cep

        # Save to database
        frame_to_database(validated_data)
        n += 1

    logger.info(f'Imported {n} frames')
