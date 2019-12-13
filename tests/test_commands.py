# Standard Library
from pathlib import Path
import shutil

# Requirements
import pytest

# Django
from django.core.management import call_command


@pytest.fixture(scope='function')
def datadir(tmp_path):
    return shutil.copytree('tests/data', tmp_path / 'data')


def test_command_output(api, db, datadir):
    path = datadir / 'cr6' / 'eton2'
    files = list(path.iterdir())

    assert call_command('import_cr6', path) == 0

    # Verify the data has been imported
    response = api.query()
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 168

    # Verify the files have been archived
    for path in files:
        assert not path.exists()
        assert Path(f'{path}.xz').exists()
