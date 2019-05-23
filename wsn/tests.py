# Standard Library
from datetime import datetime
import time

import pytest

# Django
from django.conf import settings
from django.contrib.auth import get_user_model

# Rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

# WSN
from wsn.models import Frame


@pytest.fixture
def celery_app(celery_app):
    celery_app.conf.ONCE = settings.CELERY_ONCE
    return celery_app


@pytest.fixture(scope='module')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Database intialization. Here we create the needed objects in the database.
    Since we reuse the database by default (--reuse-db), we have to use
    "get_or_create" instead of "create".
    """
    User = get_user_model()
    with django_db_blocker.unblock():
        user, created = User.objects.get_or_create(username='api')
        Token.objects.get_or_create(user=user)


class API:

    def __init__(self, client):
        self.client = client

    def create(self, data):
        path = '/api/create/'
        return self.client.post(path, data, format='json')

    def query(self, data):
        path = '/api/query/v2/'
        return self.client.get(path, data)

    def iridium(self, data):
        path = '/api/iridium/'
        return self.client.post(path, data)


@pytest.fixture
def api(transactional_db):
    token = Token.objects.get(user__username='api').key
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return API(client)



def test_create_time_required(api):
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


def test_create_time_badtype(api):
    ts = datetime.utcnow()
    response = api.create({
        'tags': {'serial': 42},
        'frames':
            [
                {'time': ts.isoformat(), 'data': {'battery': 99}},
            ]
    })
    assert response.status_code == 400


def test_create(api):
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
    response = api.query({'serial:int': 1234})
    assert response.status_code == 200
    json = response.json()
    assert len(json['results']) == 0

    # Query (hit)
    response = api.query({'serial:int': 42})
    assert response.status_code == 200
    results = response.json()['results']
    assert len(results) == 3
    last = results[-1]
    assert last['battery'] == 30
    assert last['received'] == t+2
    assert last['time'] == (now + 2)

    # Time
    response = api.query({'serial:int': 42, 'time__gte': now + 1})
    assert response.status_code == 200
    json = response.json()
    assert len(json['results']) == 2


def test_iridium(api, celery_worker, celery_app):
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
      'data': ['48656c6c6f21205468697320697320612074657374206d6573736167652066726f6d20526f636b424c4f434b21']
    }
    response = api.iridium(data)
    assert response.status_code == 200

    response = api.query({})
    results = response.json()['results']
    assert len(results) == 0

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
      'data': ['3c3d3e0640073c10fdc337de2423b77b75dee65c345d3ff8fbffffe7ffd148e13a40006cae425ceca947d25c8f124080dec6421e29aa47d300a4f03e80663640d400003c40']
    }
    response = api.iridium(data)
    assert response.status_code == 200

    response = api.query({})
    results = response.json()['results']
    assert len(results) == 1
