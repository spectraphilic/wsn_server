# Standard Library
import datetime
from pathlib import Path
import shutil
import time

# Requirements
import pytest

# Django
from django.core.management import call_command


@pytest.fixture(scope='function')
def datadir(tmp_path):
    return shutil.copytree('tests/data', tmp_path / 'data')


def test_import_eton2(api, db, datadir):
    path = datadir / 'cr6' / 'eton2'
    files = list(path.iterdir())

    # Test skipping files
    skip = int(time.time() - datetime.datetime(2018, 1, 1).timestamp()) // 60
    assert call_command('import_cr6', path, skip=skip) == 0
    # Verify no data has been imported
    response = api.query()
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 0

    # Test importing data
    assert call_command('import_cr6', path, skip=0) == 0
    # Verify the data has been imported
    response = api.query()
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 168

    # Verify the files have been archived
    for path in files:
        assert not path.exists()
        assert Path(f'{path}.xz').exists()
