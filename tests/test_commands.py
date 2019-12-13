# Standard Library
import datetime
from pathlib import Path
import shutil
import time

# Requirements
from clickhouse_driver import Client
import pytest

# Django
from django.conf import settings
from django.core.management import call_command


@pytest.fixture(scope='function')
def datadir(tmp_path):
    return shutil.copytree('tests/data', tmp_path / 'data')


@pytest.fixture(scope='function')
def clickhouse():
    client = Client(
        settings.CLICKHOUSE_HOST,
        user=settings.CLICKHOUSE_USER,
        password=settings.CLICKHOUSE_PASSWORD,
    )
    client.execute(f'CREATE DATABASE {settings.CLICKHOUSE_NAME}')
    yield
    client.execute(f'DROP DATABASE IF EXISTS {settings.CLICKHOUSE_NAME}')
    client.disconnect()


def test_import_eton2(api, db, datadir):
    path = datadir / 'cr6' / 'eton2'
    files = list(path.iterdir())

    # Test skipping files
    skip = int(time.time() - datetime.datetime(2018, 1, 1).timestamp()) // 60
    assert call_command('import_cr6', path, skip=skip) == 0
    # Verify no data has been imported
    response = api.query_pg()
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 0

    # Test importing data
    assert call_command('import_cr6', path, skip=0) == 0
    # Verify the data has been imported
    response = api.query_pg()
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 168

    # Verify the files have been archived
    for path in files:
        assert not path.exists()
        assert Path(f'{path}.xz').exists()


def test_import_finseflux(api, clickhouse, datadir):
    path = datadir / 'cr6' / 'finseflux'
    table = 'finseflux_Biomet'
    files = list(path.iterdir())

    # Test skipping files
    skip = int(time.time() - datetime.datetime(2018, 1, 1).timestamp()) // 60
    assert call_command('import_cr6', path, skip=skip) == 0

    # Test importing data
    assert call_command('import_cr6', path, skip=0) == 0
    # Verify the data has been imported
    response = api.query_ch(table)
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 288

    # Verify the files have been archived
    for path in files:
        assert not path.exists()
        assert (
            Path(f'{path}.xz').exists() or
            Path(f'{path}.empty').exists() or
            Path(f'{path}.truncated').exists()
        )
