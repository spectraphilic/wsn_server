# Standard Library
from datetime import datetime, timedelta, timezone

import dateutil

# Django
from django.contrib.auth import get_user_model

# Rest Framework
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

# WSN
from wsn.models import Frame


class CreateTestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        user = User.objects.create(username='api')
        self.token = Token.objects.create(user=user).key
        self.extra = {'HTTP_AUTHORIZATION': 'Token %s' % self.token}

    def post(self, url, data, extra):
        return self.client.post(url, data, format='json', **extra)

    def test_create_time_required(self):
        response = self.post('/wsn/api/create/',
            {
                'tags': {'serial': 42},
                'frames':
                    [
                        {'data': {'battery': 50}},
                        {'data': {'battery': 75}},
                        {'data': {'battery': 30}},
                    ]
            }, self.extra)
        self.assertEqual(response.status_code, 400)

    def test_create_timezone_required(self):
        ts = datetime.utcnow()
        response = self.post('/wsn/api/create/',
            {
                'tags': {'serial': 42},
                'frames':
                    [
                        {'time': ts.isoformat(), 'data': {'battery': 99}},
                    ]
            }, self.extra)
        self.assertEqual(response.status_code, 400)

    def test_create(self):
        # Create
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        s = timedelta(seconds=1)
        response = self.post('/wsn/api/create/',
            {
                'tags': {'serial': 42},
                'frames':
                    [
                        {'time': (now + s*0).isoformat(), 'data': {'battery': 50}},
                        {'time': (now + s*1).isoformat(), 'data': {'battery': 75}},
                        {'time': (now + s*2).isoformat(), 'data': {'battery': 30}},
                    ]
            }, self.extra)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Frame.objects.count(), 3)

        # Query (miss)
        response = self.client.get('/wsn/api/query/v2/', {'serial:int': 1234}, **self.extra)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(len(json['results']), 0)

        # Query (hit)
        response = self.client.get('/wsn/api/query/v2/', {'serial:int': 42}, **self.extra)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(len(json['results']), 3)
        out = dateutil.parser.parse(json['results'][-1]['time'])
        self.assertEqual(now, out)

        # Time
        query = {'serial:int': 42, 'time__gte': (now + s*1).timestamp()}
        response = self.client.get('/wsn/api/query/v2/', query, **self.extra)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(len(json['results']), 2)


    def test_query_bad_request(self):
        response = self.client.get('/wsn/api/query/v2/', {}, **self.extra)
        self.assertEqual(response.status_code, 400)
