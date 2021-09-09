# Standard Library
import copy
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
        {
            'time': '2019-04-06 15:10:00',
            'temperature': 22.875, 'temperature_qc': False,
            'humidity': 11.994140625, 'humidity_qc': False,
            'air_pressure': 103092.3125, 'air_pressure_qc': False,
            'snow_depth': 1203.0, 'snow_depth_qc': False,
        },
        {
            'time': '2019-04-06 15:20:00',
            'temperature': 23.4375, 'temperature_qc': False,
            'humidity': 10.7353515625, 'humidity_qc': False,
            'air_pressure': 103091.2421875, 'air_pressure_qc': False,
            'snow_depth': 1910.0, 'snow_depth_qc': False,
        },
        {
            'time': '2019-04-06 15:30:00',
            'temperature': 23.75, 'temperature_qc': False,
            'humidity': 11.0673828125, 'humidity_qc': False,
            'air_pressure': 103101.4375, 'air_pressure_qc': False,
            'snow_depth': 1237.0, 'snow_depth_qc': False,
        },
        {
            'time': '2019-04-06 15:40:00',
            'temperature': 23.9375, 'temperature_qc': False,
            'humidity': 10.7578125, 'humidity_qc': False,
            'air_pressure': 103115.2265625, 'air_pressure_qc': False,
            'snow_depth': 1254.0, 'snow_depth_qc': False,
        },
        {
            'time': '2019-04-06 15:50:00',
            'temperature': 24.0, 'temperature_qc': False,
            'humidity': 10.677734375, 'humidity_qc': False,
            'air_pressure': 103126.25, 'air_pressure_qc': False,
            'snow_depth': 1241.0, 'snow_depth_qc': False,
        },
        {
            'time': '2019-04-06 16:00:00',
            'temperature': 24.0625, 'temperature_qc': False,
            'humidity': 10.38671875, 'humidity_qc': False,
            'air_pressure': 103137.21875, 'air_pressure_qc': False,
            'snow_depth': 1243.0, 'snow_depth_qc': False,
        },
        {
            'time': '2019-04-06 16:10:00',
            'temperature': 24.125, 'temperature_qc': False,
            'humidity': 10.2158203125, 'humidity_qc': False,
            'air_pressure': 103142.921875, 'air_pressure_qc': False,
            'snow_depth': 1240.0, 'snow_depth_qc': False,
        },
        {
            'time': '2019-04-06 16:20:00',
            'temperature': 24.125, 'temperature_qc': False,
            'humidity': 10.236328125, 'humidity_qc': False,
            'air_pressure': 103160.3984375, 'air_pressure_qc': False,
            'snow_depth': 1244.0, 'snow_depth_qc': False,
        },
    ]

    for row in data:
        time = row['time']
        row['time'] = int(datetime.strptime(time, '%Y-%m-%d %H:%M:%S').timestamp())

    return data


def test_qc(data, api_key, db):
    # Prepare data
    data1 = copy.deepcopy(data[:7])
    data2 = copy.deepcopy(data[6:])
    data1[-1]['temperature'] = 0
    assert len(data) == 9
    assert len(data1) == 7
    assert len(data2) == 3

    # Verify initial state
    assert Site.objects.count() == 0
    assert Node.objects.count() == 0
    assert Data.objects.count() == 0

    # First upload
    url = reverse('api:qc-upload')
    name = 'sw-001'
    response = api_key.client.post(url, [{'name': name, 'data': data1}], format='json')
    assert response.status_code == 200
    assert len(response.data) == 1
    node = response.data[0]
    assert node['name'] == name
    assert node['data'] == data1
    assert Node.objects.count() == 1
    assert Data.objects.count() == 7
    assert Data.objects.get(node__name=name, time=1554566400).temperature == 0

    # Second upload
    response = api_key.client.post(url, [{'name': name, 'data': data2}], format='json')
    assert response.status_code == 200
    assert len(response.data) == 1
    node = response.data[0]
    assert node['name'] == name
    assert node['data'] == data
    assert Node.objects.count() == 1
    assert Data.objects.count() == 9
    assert Data.objects.get(node__name=name, time=1554566400).temperature == 24.0625
