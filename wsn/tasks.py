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
def in_iridium(self, POST):
    imei = POST['imei'] # 300234010753370
    momsn = POST['momsn'] # 12345
    transmit_time = POST['transmit_time'] # 12-10-10 10:41:50
    iridium_latitude = POST['iridium_latitude'] # 52.3867
    iridium_longitude = POST['iridium_longitude'] # 0.2938
    iridium_cep = POST['iridium_cep'] # 8
    data = POST['data'] # 48656c6c6f20576f726c6420526f636b424c4f434b
    data = codecs.decode(data, 'hex')

    # To epoch
    transmit_time = datetime.strptime(transmit_time, '%y-%m-%d %H:%M:%S')
    transmit_time = int(transmit_time).timestamp()

    # Parse data
    frame, data = waspmote.parse_frame(data)
    if frame is None:
        raise ValueError('error parsing frame')

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
