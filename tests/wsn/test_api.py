# Standard Library
from datetime import datetime
import time

# Project
from wsn.models import Frame


def test_create_time_required(api, db):
    response = api.create({
        'tags': {'serial': 42},
        'frames':
            [
                {'data': {'battery': 50}},
                {'data': {'battery': 75}},
                {'data': {'battery': 30}},
            ]
    })
    assert response.status_code == 400


def test_create_time_badtype(api, db):
    ts = datetime.utcnow()
    response = api.create({
        'tags': {'serial': 42},
        'frames':
            [
                {'time': ts.isoformat(), 'data': {'battery': 99}},
            ]
    })
    assert response.status_code == 400


def test_create(api, db):
    # Create
    now = int(time.time())
    t = int(time.time())
    response = api.create({
        'tags': {'serial': 42},
        'frames':
            [
                {'time': now + 0, 'data': {'battery': 50, 'received': t+0}},
                {'time': now + 1, 'data': {'battery': 75, 'received': t+1}},
                {'time': now + 2, 'data': {'battery': 30, 'received': t+2}},
            ]
    })
    assert response.status_code == 201
    assert Frame.objects.count() == 3
    last = Frame.objects.order_by('received').last()
    assert last.received == t+2
    assert last.data['battery'] == 30

    # Query (miss)
    response = api.query_pg({'serial:int': 1234})
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 0

    # Query (hit)
    response = api.query_pg({'serial:int': 42})
    assert response.status_code == 200
    rows = response.json()['rows']
    assert len(rows) == 3
    last = rows[-1]
    assert last['battery'] == 30
    assert last['received'] == t+2
    assert last['time'] == (now + 2)

    # Time
    response = api.query_pg({'serial:int': 42, 'time__gte': now + 1})
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 2


def test_iridium(api, db, celery_session_app, celery_session_worker):
    # Test message
    data = {
        'device_type': ['ROCKBLOCK'],
        'serial': ['10003'],
        'momsn': ['694'],
        'transmit_time': ['19-03-23 10:30:29'],
        'imei': ['300234063769210'],
        'iridium_latitude': ['49.7932'],
        'iridium_longitude': ['142.5998'],
        'iridium_cep': ['98.0'],
        'data': ['48656c6c6f21205468697320697320612074657374206d6573736167652066726f6d20526f636b424c4f434b21'],
    }
    response = api.iridium(data)
    assert response.status_code == 200

    response = api.query_pg()
    rows = response.json()['rows']
    assert len(rows) == 0

    # Frame
    data = {
        'device_type': ['ROCKBLOCK'],
        'serial': ['10003'],
        'momsn': ['694'],
        'transmit_time': ['19-03-23 10:30:29'],
        'imei': ['300234063769210'],
        'iridium_latitude': ['49.7932'],
        'iridium_longitude': ['142.5998'],
        'iridium_cep': ['98.0'],
        'data': ['3c3d3e0640073c10fdc337de2423b77b75dee65c345d3ff8fbffffe7ffd148e13a400'
                 '06cae425ceca947d25c8f124080dec6421e29aa47d300a4f03e80663640d400003c40'],
    }
    response = api.iridium(data)
    assert response.status_code == 200

    response = api.query_pg()
    json = response.json()
    assert 'rows' in json
    assert len(json['rows']) == 1


def test_4G(api, db, celery_session_app, celery_session_worker):
    data = {
        'frame': '3C3D3E0640073C10FDC337DE2423B77B75DEE65C345D3FF8FBFFFFE7FFD148E13A400'
                 '06CAE425CECA947D25C8F124080DEC6421E29AA47D300A4F03E80663640D400003C40',
    }
    response = api.meshlium(data)
    assert response.status_code == 200

    response = api.query_pg()
    json = response.json()
    assert 'rows' in json
    assert len(json['rows']) == 1
