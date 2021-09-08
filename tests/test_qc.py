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
    assert Site.objects.count() == 0
    assert Node.objects.count() == 0
    assert Data.objects.count() == 0

    # First upload
    url = reverse('api:qc-upload')
    name = 'sw-001'
    response = api.client.post(url, [{'name': name, 'data': data}], format='json')
    assert response.status_code == 200
    assert len(response.data) == 1
    node = response.data[0]
    assert node['name'] == name
    assert node['data'] == data
    assert Node.objects.count() == 1
    assert Data.objects.count() == 1

    # Second upload
    response = api.client.post(url, [{'name': name, 'data': data}], format='json')
    assert response.status_code == 200
    assert len(response.data) == 1
    node = response.data[0]
    assert node['name'] == name
    assert node['data'] == data
    assert Node.objects.count() == 1
    assert Data.objects.count() == 1
