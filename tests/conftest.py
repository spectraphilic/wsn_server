"""
Writing these tests has been harder than I expected. Follows a description of
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

import pytest

# Django
from django.conf import settings
from django.contrib.auth import get_user_model

# Django REST framework
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token


class API:

    def __init__(self, client):
        self.client = client

    def create(self, data):
        path = '/api/create/'
        return self.client.post(path, data, format='json')

    def query_pg(self, data=None):
        path = '/api/query/postgresql/'
        return self.client.get(path, data)

    def query_ch(self, table, data=None):
        data = data or {}
        data['table'] = table

        path = '/api/query/clickhouse/'
        return self.client.get(path, data)

    def iridium(self, data):
        path = '/api/iridium/'
        return self.client.post(path, data)

    def meshlium(self, data):
        path = '/getpost_frame_parser.php'
        return self.client.post(path, data)


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


@pytest.fixture(scope='module')
def api():
    client = APIClient()
    return API(client)


@pytest.fixture(scope='module')
def api_user(django_db_setup):
    """
    We depend on django_db_setup to be sure this fixture is run on the test
    database, not the real database.
    """
    token = Token.objects.get(user__username='api')
    token = token.key

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
    return API(client)
