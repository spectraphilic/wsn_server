# Standard Library
from datetime import datetime

# Requirements
import pytest
from rest_framework.reverse import reverse

# Project
from qc.models import Site, Node, Data




@pytest.fixture
def data():
    data = [
        {
            'time': '2019-04-06 15:00:00',
            'temperature': 22.6875, 'temperature_qc': False,
            'humidity': 12.080078125, 'humidity_qc': False,
            'air_pressure': 103088.1640625, 'air_pressure_qc': False,
            'snow_depth': 2165.0, 'snow_depth_qc': False,
        },
    ]

    for row in data:
        time = row['time']
        row['time'] = int(datetime.strptime(time, '%Y-%m-%d %H:%M:%S').timestamp())

    return data


def test_qc(data, api, db):
#   site = Site.objects.create(name='Ny-Ålesund')
#   node = Node.objects.create(name='sw-001', site=site)
#   assert Site.objects.count() == 1
#   assert Node.objects.count() == 1
#   assert Data.objects.count() == 0

    url = reverse('api:qc-upload')
    response = api.client.post(url, {'name': 'sw-001', 'data': data}, format='json')
    print()
    print('XXX', response.status_code)
    print(response.data)

#   assert Node.objects.count() == 1
#   assert Data.objects.count() == 1
