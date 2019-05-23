# Standard Library
from datetime import datetime
import time

import pytest

# Django
from django.contrib.auth import get_user_model

# Rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

# WSN
from wsn.models import Frame


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


@pytest.fixture
def client(db):
    token = Token.objects.get(user__username='api').key
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return client


@pytest.fixture
def api_create(client):
    path = '/api/create/'
    def post_json(data):
        response = client.post(path, data, format='json')
        return response

    return post_json


def test_create_time_required(api_create):
    response = api_create({
        'tags': {'serial': 42},
        'frames':
            [
                {'data': {'battery': 50}},
                {'data': {'battery': 75}},
                {'data': {'battery': 30}},
            ]
    })
    assert response.status_code == 400


def test_create_time_badtype(api_create):
    ts = datetime.utcnow()
    response = api_create({
        'tags': {'serial': 42},
        'frames':
            [
                {'time': ts.isoformat(), 'data': {'battery': 99}},
            ]
    })
    assert response.status_code == 400


def test_create(client, api_create):
    # Create
    now = int(time.time())
    t = int(time.time())
    response = api_create({
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
    response = client.get('/api/query/v2/', {'serial:int': 1234})
    assert response.status_code == 200
    json = response.json()
    assert len(json['results']) == 0

    # Query (hit)
    response = client.get('/api/query/v2/', {'serial:int': 42})
    assert response.status_code == 200
    results = response.json()['results']
    assert len(results) == 3
    last = results[-1]
    assert last['battery'] == 30
    assert last['received'] == t+2
    assert last['time'] == (now + 2)

    # Time
    query = {'serial:int': 42, 'time__gte': now + 1}
    response = client.get('/api/query/v2/', query)
    assert response.status_code == 200
    json = response.json()
    assert len(json['results']) == 2
