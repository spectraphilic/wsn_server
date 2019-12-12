"""
Writing these tests has been harder that I expected. Follows a description of
the chain of choices, problems, and solutions.

Choice: We want to reuse fixtures to speed up tests.
Problem: Transactional tests truncate all tables, see
https://docs.djangoproject.com/en/2.2/topics/testing/tools/#django.test.TransactionTestCase
Solution: Don't use transactional tests.

Problem: With non-transactional tests, the celery_worker fixture closes the
database connections, this is a known problem, see
https://github.com/celery/celery/issues/4511
Solution: Use celery_session_worker instead.

Problem: The celery_session_worker fixture won't have access to the database
because started too early. This is the consequence of pytest-django
"conservative approach"
https://pytest-django.readthedocs.io/en/latest/database.html#database-creation-re-use
Solution: Override the django_db_blocker fixture to allow general access to the
database.

Problem: By default tests won't rollback the transaction.
Solution: Depend on the db fixture in tests that modify the database.

Problem: If there's an error in a Celery task, we want to see error as a normal
traceback when running the tests.
Solution: Run tasks synchronously (task_always_eager), propagate errors
(task_eager_propagates), and don't retry (CELERY_TASK_MAX_RETRIES = 0).
"""

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


@pytest.fixture(scope='session')
def celery_session_app(celery_session_app):
    celery_session_app.conf.ONCE = settings.CELERY_ONCE

    # Run tasks synchronously and propagate errors to have meaningful
    # tracebacks.
    celery_session_app.conf.task_always_eager = True
    celery_session_app.conf.task_eager_propagates = True

    return celery_session_app


@pytest.fixture(scope='session')
def django_db_blocker(django_db_blocker):
    """
    Allow general access to the database. This way tasks running from the
    celery_session_worker will have access to the database.
    """
    django_db_blocker.unblock()
    return django_db_blocker


@pytest.fixture(scope='module')
def django_db_setup(django_db_setup):
    """
    Database intialization. Here we create the needed objects in the database.
    Since we reuse the database by default (--reuse-db), we have to use
    "get_or_create" instead of "create".
    """
    User = get_user_model()
    user, created = User.objects.get_or_create(username='api')
    Token.objects.get_or_create(user=user)


class API:

    def __init__(self, client):
        self.client = client

    def create(self, data):
        path = '/api/create/'
        return self.client.post(path, data, format='json')

    def query(self, data):
        path = '/api/query/postgresql/'
        return self.client.get(path, data)

    def iridium(self, data):
        path = '/api/iridium/'
        return self.client.post(path, data)

    def meshlium(self, data):
        path = '/getpost_frame_parser.php'
        return self.client.post(path, data)


@pytest.fixture(scope='module')
def api(django_db_setup):
    """
    We depend on django_db_setup to be sure this fixture is run on the test
    database, not the real database.
    """
    token = Token.objects.get(user__username='api')
    token = token.key

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return API(client)


#
# Tests start here
#


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
    response = api.query({'serial:int': 1234})
    assert response.status_code == 200
    json = response.json()
    from pprint import pprint
    pprint(json)
    assert len(json['rows']) == 0

    # Query (hit)
    response = api.query({'serial:int': 42})
    assert response.status_code == 200
    rows = response.json()['rows']
    assert len(rows) == 3
    last = rows[-1]
    assert last['battery'] == 30
    assert last['received'] == t+2
    assert last['time'] == (now + 2)

    # Time
    response = api.query({'serial:int': 42, 'time__gte': now + 1})
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

    response = api.query({})
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

    response = api.query({})
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

    response = api.query({})
    json = response.json()
    assert 'rows' in json
    assert len(json['rows']) == 1
