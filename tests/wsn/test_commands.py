import datetime
import shutil
import socket
import time
from pathlib import Path

# Requirements
import pytest
from clickhouse_driver import Client

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
    rows = json['rows']
    assert len(rows) == 288

    # Verify first row
    rows = [dict(zip(json['columns'], row)) for row in json['rows']]
    datetime.datetime.fromtimestamp(1566585010).strftime("%Y-%m-%d %H:%M:%S")
    row = rows[0]
    row['TIMESTAMP'] = datetime.datetime.fromtimestamp(row.pop('time')).strftime("%Y-%m-%d %H:%M:%S")
    assert row == {
        "TIMESTAMP": "2019-08-23 18:30:10",
        "RECORD": 2671295,
        "PA_4_2_1_1_1": 88.20268,
        "VIN_18_39_1_1_1": 13.72415,
        "RH_19_3_1_2_1": 81.23672,
        "TA_2_1_1_1_1": 7.452743,
        "TA_2_1_1_2_1": 7.451554,
        "TS_2_38_1_1_1": 7.6,
        "TSS_2_99_1_1_1": 6.88938,
        "RH_19_3_1_1_1": 78.38431,
        "WS_16_33_1_1_1": 2.4,
        "WD_20_35_1_1_1": 292,
        "METNORR_99_99_1_1_1": 0,
        "METNOR_99_99_1_1_1": 322.3318,
        "METNOS_99_99_1_1_1": -0.05,
        "SWIN_6_10_1_1_1": 2.943324,
        "SWOUT_6_11_1_1_1": -3.187594,
        "LWIN_6_14_1_1_1": 341.3317,
        "LWOUT_6_15_1_1_1": 349.3209,
        "TS_2_38_2_1_1": 9.753471,
        "SWC_12_36_3_1_1": 0.3116,
        "BEC_99_99_3_1_1": 0.0031,
        "TS_2_38_3_1_1": 7.6842,
        "PERMITTIVITY_99_99_3_1_1": 17.4279,
        "CS650PERIOD_99_99_3_1_1": 3.1388,
        "CS650VRATIO_99_99_3_1_1": 1.0094,
        "SHF_6_37_1_1_1": 6.551487,
        "SHF_6_37_2_1_1": 7.361422,
        "SHF_99_37_1_1_2": 0.2802892,
        "SHF_99_37_2_1_2": 0.3256016,
        "FC1DRIFTmin_99_99_1_1_1": 0.001,
        "FC1DRIFTmean_99_99_1_1_1": 0.001,
        "FC1DRIFTmax_99_99_1_1_1": 0.001,
        "FC1DRIFTstd_99_99_1_1_1": 0,
        "FC1DRIFTsum_99_99_1_1_1": 0.006,
        "FC1WSmin_16_99_1_1_1": 2.215,
        "FC1WSmean_16_99_1_1_1": 2.215,
        "FC1WSmax_16_99_1_1_1": 2.2925,
        "FC2DRIFTmin_99_99_1_1_1": 0,
        "FC2DRIFTmean_99_99_1_1_1": 0,
        "FC2DRIFTmax_99_99_1_1_1": 0,
        "FC2DRIFTstd_99_99_1_1_1": 0,
        "FC2DRIFTsum_99_99_1_1_1": 0.001,
        "FC2WSmin_16_99_1_1_1": 3.798056,
        "FC2WSmean_16_99_1_1_1": 3.863056,
        "FC2WSmax_16_99_1_1_1": 3.929722,
    }

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
