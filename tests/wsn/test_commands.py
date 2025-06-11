# Standard Library
import datetime
from pathlib import Path
import shutil
import socket
import time

# Requirements
from clickhouse_driver import Client
import pytest

# Django
from django.conf import settings
from django.core.management import call_command


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    has_clickhouse = sock.connect_ex(('', 9000)) == 0

requires_clickhouse = pytest.mark.skipif(not has_clickhouse, reason='Requires ClickHouse running at port 9000')


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
    client.execute(f'DROP DATABASE IF EXISTS {settings.CLICKHOUSE_NAME}')
    client.execute(f'CREATE DATABASE {settings.CLICKHOUSE_NAME}')
    client.disconnect()


def test_import_eton2(api_user, db, datadir):
    path = datadir / 'cr6' / 'eton2'
    files = list(path.iterdir())

    config = datadir / 'config.toml'
    name = 'eton2'

    # Test skipping files
    skip = int(time.time() - datetime.datetime(2018, 1, 1).timestamp()) // 60
    assert call_command('import_file', config, name=name, root=datadir, skip=skip) == 0
    # Verify no data has been imported
    response = api_user.query_pg()
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 0

    # Test importing data
    assert call_command('import_file', config, name=name, root=datadir, skip=0) == 0
    # Verify the data has been imported
    response = api_user.query_pg()
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 168

    # Verify the files have been archived
    for path in files:
        assert not path.exists()
        assert Path(f'{path}.xz').exists()


@requires_clickhouse
def test_import_finseflux(api_user, clickhouse, datadir):
    path = datadir / 'cr6' / 'finseflux'
    files = list(path.iterdir())

    config = datadir / 'config.toml'
    name = 'finseflux_Biomet'

    # Test skipping files
    skip = int(time.time() - datetime.datetime(2018, 1, 1).timestamp()) // 60
    assert call_command('import_file', config, name=name, root=datadir, skip=skip) == 0

    # Test importing data
    assert call_command('import_file', config, name=name, root=datadir, skip=0) == 0
    # Verify the data has been imported
    response = api_user.query_ch(name)
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 288

    # Verify the files have been archived
    prefix = 'Biomet_'
    for path in files:
        if path.name.startswith(prefix):
            assert not path.exists()
            assert (
                Path(f'{path}.xz').exists() or
                Path(f'{path}.empty').exists() or
                Path(f'{path}.truncated').exists()
            )
        else:
            assert path.exists()


@requires_clickhouse
def test_import_hfdata(api_user, clickhouse, datadir):
    path = datadir / 'cr6' / 'finseflux'
    files = list(path.iterdir())

    config = datadir / 'config.toml'
    name = 'finseflux_HFData'

    # Test skipping files
    skip = int(time.time() - datetime.datetime(2018, 1, 1).timestamp()) // 60
    assert call_command('import_file', config, name=name, root=datadir, skip=skip) == 0

    # Test importing data
    assert call_command('import_file', config, name=name, root=datadir, skip=0) == 0
    # Verify the data has been imported
    response = api_user.query_ch(name)
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 2399

    # Verify the files have been archived
    prefix = 'HFData_'
    for path in files:
        if path.name.startswith(prefix):
            assert not path.exists()
            assert (
                Path(f'{path}.xz').exists() or
                Path(f'{path}.empty').exists() or
                Path(f'{path}.truncated').exists()
            )
        else:
            assert path.exists()


@requires_clickhouse
def test_import_sommer(api_user, clickhouse, datadir):
    path = datadir / 'sommer'
    files = list(path.iterdir())

    config = datadir / 'config.toml'
    name = 'finse_sommer'

    # Test skipping files
    skip = int(time.time() - datetime.datetime(2018, 1, 1).timestamp()) // 60
    assert call_command('import_file', config, root=datadir, name=name, skip=skip) == 0

    # Test importing data
    assert call_command('import_file', config, root=datadir, name=name, skip=0) == 0
    # Verify the data has been imported
    response = api_user.query_ch(name)
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 30

    # Verify the files have been archived
    for path in files:
        assert not path.exists()
        assert (
            Path(f'{path}.xz').exists() or
            Path(f'{path}.empty').exists() or
            Path(f'{path}.truncated').exists()
        )
