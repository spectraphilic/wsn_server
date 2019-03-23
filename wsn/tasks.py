# Standard Library
import codecs
from datetime import datetime

# Celery
from celery import shared_task

# App
from .models import frame_to_database
from .parsers import waspmote


@shared_task(
    acks_late=True,             # Send ack at the end, not the beginning
    autoretry_for=(Exception,), # Retry for any exception
    max_retries=None,           # Retry for ever
    default_retry_delay=300,    # Retry after 5min (default is 3 minutes)
)
def in_iridium(POST):
    """
    Real example:
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

    def get(name, t):
        value = POST[name]
        assert type(value) is list and len(value) == 0
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
    transmit_time = datetime.strptime(transmit_time, '%y-%m-%d %H:%M:%S')
    transmit_time = int(transmit_time).timestamp()

    # Parse data
    frame, data = waspmote.parse_frame(data)
    if frame is None:
        raise ValueError('error parsing frame')

    validated_data = waspmote.data_to_json(frame)

    # Add metadata
    tags = validated_data['tags']
    tags['device_type'] = device_type
    tags['imei'] = imei
    tags['serial'] = serial

    # Add data
    frame = validated_data['frames'][0]
    frame['momsn'] = momsn # This is a lot like motes 'frame' but uses 2 bytes
    frame['received'] = transmit_time # FIXME Convert to epoch
    frame['iridium_latitude'] = iridium_latitude
    frame['iridium_longitude'] = iridium_longitude
    frame['iridium_cep'] = iridium_cep

    # Save to database
    frame_to_database(validated_data)
