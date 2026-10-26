import datetime
import fcntl
import lzma
import shutil
import socket
import time
import tomllib
from pathlib import Path

# Requirements
import pytest
from clickhouse_driver import Client

# Django
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError

# Project
from wsn.clickhouse import ClickHouse
from wsn.models import ImportFile
from wsn.parsers.cr6 import CR6Parser

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    has_clickhouse = sock.connect_ex(('', 9000)) == 0

requires_clickhouse = pytest.mark.skipif(not has_clickhouse, reason='Requires ClickHouse running at port 9000')


def is_archived(path):
    """The file has been archived under <dir>/archive/<YYYY>/<MM>/"""
    archive = path.parent / 'archive'
    return archive.is_dir() and len(list(archive.rglob(path.name + '.xz'))) == 1


@pytest.fixture(scope='function')
def datadir(tmp_path):
    datadir = shutil.copytree('tests/data', tmp_path / 'data')
    # Rewrite the import config with absolute paths into the copied data dir
    config = datadir / 'config.toml'
    lines = []
    for line in config.read_text().splitlines():
        if line.startswith('path = "'):
            path = line.removeprefix('path = "').removesuffix('"')
            line = f'path = "{datadir / path}"'
        lines.append(line)
    config.write_text('\n'.join(lines) + '\n')
    return datadir


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
    assert call_command('import_file', config, name=name, skip=skip) == 0
    # Verify no data has been imported
    response = api_user.query_pg()
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 0

    # Test importing data
    assert call_command('import_file', config, name=name, skip=0) == 0
    # Verify the data has been imported
    response = api_user.query_pg()
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 168

    # Verify the files have been archived
    for path in files:
        assert not path.exists()
        assert is_archived(path)


def test_import_lock(datadir):
    # A second import_file run must fail loudly while another one holds
    # the lock (e.g. overlapping cron jobs).
    lockpath = settings.BASE_DIR / 'var' / 'run' / 'import_file.lock'
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    config = datadir / 'config.toml'

    with open(lockpath, 'w') as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(CommandError, match='another import_file run'):
            call_command('import_file', config, name='eton2', skip=0)


def test_import_empty_file(tmp_path):
    # Empty files are deleted, not renamed to .empty
    directory = tmp_path / 'cr6' / 'eton2'
    directory.mkdir(parents=True)
    empty_file = directory / 'Eton2_2018-01-01_00-00-00_0.dat'
    empty_file.touch()

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.eton2]
path = "{directory}"
pattern = "*.dat"
database = "postgres"
''')

    assert call_command('import_file', config, name='eton2', skip=0) == 0
    assert not empty_file.exists()
    assert not Path(f'{empty_file}.empty').exists()


DATA = Path('tests/data/cr6/finseflux')

def test_file_archive(db, tmp_path):
    directory = tmp_path / 'finseflux'
    directory.mkdir(parents=True)

    good = directory / 'HFData_2025-06-10_15-10-00_2894.dat'
    shutil.copy(DATA / good.name, good)
    truncated = directory / 'Biomet_2019-08-23_19-05-00_8362_truncated.dat'
    shutil.copy(DATA / truncated.name, truncated)
    empty = directory / 'Biomet_2019-08-23_19-05-00_8362_empty.dat'
    shutil.copy(DATA / empty.name, empty)
    # No date in the filename, cannot be archived
    undated = directory / 'UIO_Constants_Eton2_1.dat'
    undated.touch()
    # Does not match the pattern
    notes = directory / 'notes.txt'
    notes.touch()

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.test]
path = "{directory}"
pattern = "*.dat"
pipeline = "archive_first"
''')

    # Test skipping files
    skip = int(time.time() - datetime.datetime(2018, 1, 1).timestamp()) // 60
    assert call_command('file_archive', config, name='test', skip=skip) == 0
    assert good.exists()
    assert ImportFile.objects.count() == 0

    # Test archiving files
    assert call_command('file_archive', config, name='test', skip=0) == 0

    # The good file has been archived and registered
    assert not good.exists()
    assert is_archived(good)
    obj = ImportFile.objects.get()
    assert obj.name == 'test'
    assert obj.path == '2025/06/HFData_2025-06-10_15-10-00_2894.dat.xz'
    assert obj.status == ImportFile.Status.PENDING
    assert obj.error == ''
    assert obj.created_at is not None and obj.updated_at is not None

    # Quarantined files get no row
    assert not truncated.exists()
    assert Path(f'{truncated}.truncated').exists()
    assert not empty.exists()
    assert not Path(f'{empty}.empty').exists()

    # Undated and non-matching files are left in place, get no row
    assert undated.exists()
    assert notes.exists()
    assert ImportFile.objects.count() == 1


def test_file_archive_duplicate(db, tmp_path):
    directory = tmp_path / 'finseflux'
    directory.mkdir(parents=True)
    good = directory / 'HFData_2025-06-10_15-10-00_2894.dat'
    shutil.copy(DATA / good.name, good)

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.test_a]
path = "{directory}"
pattern = "*.dat"
pipeline = "archive_first"

[import.test_b]
path = "{directory}"
pattern = "*.dat"
pipeline = "archive_first"
''')

    # Archive under the first entry
    assert call_command('file_archive', config, name='test_a', skip=0) == 0
    assert not good.exists()
    assert ImportFile.objects.filter(name='test_a').count() == 1

    # The same file re-uploaded is skipped: not archived again, no new row
    shutil.copy(DATA / good.name, good)
    assert call_command('file_archive', config, name='test_a', skip=0) == 0
    assert good.exists()
    assert ImportFile.objects.count() == 1

    # The same filename under another entry is a different row
    assert call_command('file_archive', config, name='test_b', skip=0) == 0
    assert not good.exists()
    assert is_archived(good)
    assert ImportFile.objects.count() == 2
    assert ImportFile.objects.filter(name='test_b').count() == 1


def test_file_archive_pipeline(db, tmp_path, capsys):
    # Entries with pipeline="archive_first" are handled by file_archive only,
    # entries with pipeline="archive_only" are archived but never imported,
    # entries without a pipeline key or with pipeline="import_first" are
    # handled by import_file only, and an empty value disables the entry.
    old_dir = tmp_path / 'old'
    old_dir.mkdir()
    old_file = old_dir / 'Eton2_2018-01-01_00-00-00_1.dat'
    old_file.touch()

    new_dir = tmp_path / 'new'
    new_dir.mkdir()
    new_file = new_dir / 'new_HFData_2025-06-10_15-10-00_2894.dat'
    shutil.copy(DATA / 'HFData_2025-06-10_15-10-00_2894.dat', new_file)

    ao_dir = tmp_path / 'archive_only'
    ao_dir.mkdir()
    ao_file = ao_dir / 'ao_HFData_2025-06-10_15-10-00_2894.dat'
    shutil.copy(DATA / 'HFData_2025-06-10_15-10-00_2894.dat', ao_file)

    disabled_dir = tmp_path / 'disabled'
    disabled_dir.mkdir()
    disabled_file = disabled_dir / 'disabled_HFData_2025-06-10_15-10-00_2894.dat'
    shutil.copy(DATA / 'HFData_2025-06-10_15-10-00_2894.dat', disabled_file)

    typo_dir = tmp_path / 'typo'
    typo_dir.mkdir()
    typo_file = typo_dir / 'typo_HFData_2025-06-10_15-10-00_2894.dat'
    shutil.copy(DATA / 'HFData_2025-06-10_15-10-00_2894.dat', typo_file)

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.old_entry]
path = "{old_dir}"
pattern = "*.dat"

[import.new_entry]
path = "{new_dir}"
pattern = "*.dat"
pipeline = "archive_first"

[import.ao_entry]
path = "{ao_dir}"
pattern = "*.dat"
pipeline = "archive_only"

[import.disabled_entry]
path = "{disabled_dir}"
pattern = "*.dat"
pipeline = ""

[import.typo_entry]
path = "{typo_dir}"
pattern = "*.dat"
pipeline = "archve_first"
''')

    # file_archive processes only archive_first and archive_only entries
    assert call_command('file_archive', config, skip=0) == 0
    assert old_file.exists()
    assert not new_file.exists()
    assert is_archived(new_file)
    assert not ao_file.exists()
    assert is_archived(ao_file)
    # The archive_only file is registered nowhere
    assert ImportFile.objects.count() == 1
    # Disabled and unknown entries are left alone, the typo is reported
    assert disabled_file.exists()
    assert typo_file.exists()
    assert 'unknown pipeline value' in capsys.readouterr().err

    # import_file skips entries with a pipeline key other than import_first
    assert call_command('import_file', config, skip=0) == 0
    assert not old_file.exists() # Deleted, it is empty
    assert is_archived(new_file)
    assert disabled_file.exists()
    assert typo_file.exists()
    assert ImportFile.objects.count() == 1

    # file_register only walks archive_first entries
    assert call_command('file_register', config) == 0
    assert ImportFile.objects.count() == 1


def test_import_file_pipeline(db, tmp_path):
    # pipeline = "import_first" selects the old pipeline explicitly, and an
    # empty value disables the entry; both are different from the key being
    # absent.
    directory = tmp_path / 'data'
    directory.mkdir()
    first = directory / 'first_Eton2_2018-01-01_00-00-00_1.dat'
    first.touch()
    disabled = directory / 'disabled_Eton2_2018-01-01_00-00-00_2.dat'
    disabled.touch()

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.first_entry]
path = "{directory}"
pattern = "first_*.dat"
pipeline = "import_first"

[import.disabled_entry]
path = "{directory}"
pattern = "disabled_*.dat"
pipeline = ""
''')

    assert call_command('import_file', config, skip=0) == 0
    assert not first.exists() # Deleted, it is empty
    assert disabled.exists()
    assert ImportFile.objects.count() == 0


def test_file_archive_only(db, tmp_path):
    # Entries with pipeline="archive_only" are archived but not registered;
    # quarantine behavior is the same as for pipeline="archive".
    directory = tmp_path / 'finseflux'
    directory.mkdir(parents=True)

    good = directory / 'HFData_2025-06-10_15-10-00_2894.dat'
    shutil.copy(DATA / good.name, good)
    truncated = directory / 'Biomet_2019-08-23_19-05-00_8362_truncated.dat'
    shutil.copy(DATA / truncated.name, truncated)

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.test]
path = "{directory}"
pattern = "*.dat"
pipeline = "archive_only"
''')

    assert call_command('file_archive', config, skip=0) == 0

    # Archived but not registered
    assert not good.exists()
    assert is_archived(good)
    assert ImportFile.objects.count() == 0

    # Quarantine unchanged
    assert not truncated.exists()
    assert Path(f'{truncated}.truncated').exists()
    assert ImportFile.objects.count() == 0


def test_file_archive_future_date(db, tmp_path, capsys):
    # A file with a filename date more than 2 days in the future means the
    # logger's clock is wrong: it is renamed aside, like truncated files,
    # on both archive_first and archive_only entries
    directory = tmp_path / 'eton2'
    directory.mkdir(parents=True)
    only = tmp_path / 'only'
    only.mkdir()
    data = (ETON2 / 'uio_data_cr6_2019_05_20_1300.dat').read_bytes()

    far = datetime.date.today() + datetime.timedelta(days=10)
    near = datetime.date.today() + datetime.timedelta(days=1)
    far_name = f'HFData_{far:%Y-%m-%d}_01-00-00_1.dat'
    near_name = f'HFData_{near:%Y-%m-%d}_01-00-00_1.dat'
    only_name = f'HFData_{far:%Y-%m-%d}_02-00-00_2.dat'
    (directory / far_name).write_bytes(data)
    (directory / near_name).write_bytes(data)
    (only / only_name).write_bytes(data)

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.eton2]
path = "{directory}"
pattern = "*.dat"
database = "postgres"
pipeline = "archive_first"

[import.test_only]
path = "{only}"
pattern = "*.dat"
pipeline = "archive_only"
''')

    assert call_command('file_archive', config, skip=0) == 0
    captured = capsys.readouterr()

    # The future-dated file is renamed aside and not registered
    assert not (directory / far_name).exists()
    assert (directory / f'{far_name}.future').exists()
    assert 'WARNING' in captured.err
    assert 'future' in captured.err

    # A file within the window is archived and registered normally
    assert not (directory / near_name).exists()
    assert ImportFile.objects.filter(name='eton2').count() == 1

    # Same on archive_only entries: renamed aside, not archived
    assert not (only / only_name).exists()
    assert (only / f'{only_name}.future').exists()
    assert not is_archived(only / only_name)


def test_file_archive_lock(tmp_path):
    # A second file_archive run must fail loudly while another one holds
    # the lock (e.g. overlapping cron jobs).
    lockpath = settings.BASE_DIR / 'var' / 'run' / 'file_archive.lock'
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    config = tmp_path / 'config.toml'
    config.write_text('[import]\n')

    with open(lockpath, 'w') as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(CommandError, match='another file_archive run'):
            call_command('file_archive', config)


ETON2 = Path('tests/data/cr6/eton2')

def archived_path(config, obj):
    """The path of the archived file a row refers to."""
    with open(config, 'rb') as f:
        values = tomllib.load(f)['import'][obj.name]
    return Path(values['path']) / 'archive' / obj.path


@pytest.fixture
def archived(tmp_path):
    """
    Archive the eton2 data files and return the config path.
    """
    directory = tmp_path / 'eton2'
    directory.mkdir(parents=True)
    for path in ETON2.iterdir():
        shutil.copy(path, directory / path.name)

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.eton2]
path = "{directory}"
pattern = "*.dat"
database = "postgres"
pipeline = "archive_first"
''')
    assert call_command('file_archive', config, skip=0) == 0
    return config


def test_file_import(api_user, db, archived):
    config = archived

    # Nothing has been imported yet
    response = api_user.query_pg()
    assert response.status_code == 200
    assert len(response.json()['rows']) == 0
    assert ImportFile.objects.get().status == ImportFile.Status.PENDING

    # Import the archived file
    assert call_command('file_import', config) == 0
    response = api_user.query_pg()
    assert len(response.json()['rows']) == 168
    obj = ImportFile.objects.get()
    assert obj.status == ImportFile.Status.DONE
    assert obj.error == ''
    assert obj.updated_at >= obj.created_at

    # A second run has nothing pending
    assert call_command('file_import', config) == 0
    response = api_user.query_pg()
    assert len(response.json()['rows']) == 168
    assert ImportFile.objects.filter(status=ImportFile.Status.DONE).count() == 1


def test_file_import_name(db, archived):
    # Rows of other entries are left pending
    assert call_command('file_import', archived, name='other') == 0
    assert ImportFile.objects.get().status == ImportFile.Status.PENDING

    assert call_command('file_import', archived, name='eton2') == 0
    assert ImportFile.objects.get().status == ImportFile.Status.DONE


def test_file_import_permanent_error(db, archived):
    # A corrupted archive cannot be parsed: the row is marked as error
    config = archived
    obj = ImportFile.objects.get()
    archived_path(config, obj).write_bytes(b'this is not an xz file')

    assert call_command('file_import', config) == 0
    obj.refresh_from_db()
    assert obj.status == ImportFile.Status.ERROR
    assert obj.error != ''


def test_file_import_transient(db, tmp_path, archived, monkeypatch):
    config = archived
    obj = ImportFile.objects.get()

    # An entry missing from the config leaves the row pending
    other = tmp_path / 'other.toml'
    other.write_text('[import]\n')
    assert call_command('file_import', other) == 0
    obj.refresh_from_db()
    assert obj.status == ImportFile.Status.PENDING

    # An upload failure leaves the row pending
    with monkeypatch.context() as m:
        def fail(*args, **kwargs):
            raise ConnectionError('database is down')
        m.setattr('wsn.management.commands.file_import.upload2pg', fail)
        assert call_command('file_import', config) == 0
    obj.refresh_from_db()
    assert obj.status == ImportFile.Status.PENDING

    # A missing archived file leaves the row pending
    archived_path(config, obj).unlink()
    assert call_command('file_import', config) == 0
    obj.refresh_from_db()
    assert obj.status == ImportFile.Status.PENDING


def test_file_import_bad_timestamp(db, api_user, tmp_path, capsys):
    # A row with a timestamp too far from the filename date is skipped
    directory = tmp_path / 'eton2'
    directory.mkdir(parents=True)
    src = ETON2 / 'uio_data_cr6_2019_05_20_1300.dat'
    dst = directory / src.name
    data = src.read_bytes()
    assert data.count(b'"2019-05-20 13:00:00"') == 1
    dst.write_bytes(data.replace(b'"2019-05-20 13:00:00"', b'"2001-01-01 00:00:00"'))

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.eton2]
path = "{directory}"
pattern = "*.dat"
database = "postgres"
pipeline = "archive_first"
''')

    assert call_command('file_archive', config, skip=0) == 0
    assert call_command('file_import', config) == 0
    captured = capsys.readouterr()
    assert 'WARNING 1 row(s) skipped' in captured.err
    assert '2001-01-01' in captured.err

    response = api_user.query_pg()
    assert len(response.json()['rows']) == 167
    obj = ImportFile.objects.get()
    assert obj.status == ImportFile.Status.DONE
    assert obj.error == ''


def test_file_import_future_timestamp(db, api_user, tmp_path, capsys):
    # A row with a timestamp far in the future, like the ones found in
    # mobileflux files, is skipped
    directory = tmp_path / 'eton2'
    directory.mkdir(parents=True)
    src = ETON2 / 'uio_data_cr6_2019_05_20_1300.dat'
    dst = directory / src.name
    data = src.read_bytes()
    assert data.count(b'"2019-05-23 12:00:00"') == 1
    dst.write_bytes(data.replace(b'"2019-05-23 12:00:00"', b'"2028-01-01 00:00:00"'))

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.eton2]
path = "{directory}"
pattern = "*.dat"
database = "postgres"
pipeline = "archive_first"
''')

    assert call_command('file_archive', config, skip=0) == 0
    assert call_command('file_import', config) == 0
    captured = capsys.readouterr()
    assert 'WARNING 1 row(s) skipped' in captured.err
    assert '2028-01-01' in captured.err

    response = api_user.query_pg()
    assert len(response.json()['rows']) == 167


def test_file_import_no_filename_date(db, api_user, tmp_path):
    # Archives with no date in their name, from the old pipeline and
    # registered by file_register, import fine: validation does not use
    # the filename
    directory = tmp_path / 'data'
    archive = directory / 'archive' / '2019' / '05'
    archive.mkdir(parents=True)
    data = (ETON2 / 'uio_data_cr6_2019_05_20_1300.dat').read_bytes()
    with lzma.open(archive / 'uio_data_cr6.dat.xz', 'wb') as f:
        f.write(data)

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.eton2]
path = "{directory}"
pattern = "*.dat"
database = "postgres"
pipeline = "archive_first"
''')

    assert call_command('file_register', config) == 0
    assert call_command('file_import', config) == 0
    response = api_user.query_pg()
    assert len(response.json()['rows']) == 168


def test_file_import_lock(tmp_path):
    # A second file_import run must fail loudly while another one holds
    # the lock (e.g. overlapping cron jobs).
    lockpath = settings.BASE_DIR / 'var' / 'run' / 'file_import.lock'
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    config = tmp_path / 'config.toml'
    config.write_text('[import]\n')

    with open(lockpath, 'w') as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(CommandError, match='another file_import run'):
            call_command('file_import', config)


@requires_clickhouse
def test_file_import_clickhouse(api_user, clickhouse, db, tmp_path):
    directory = tmp_path / 'finseflux'
    directory.mkdir(parents=True)
    shutil.copy(
        DATA / 'Biomet_2019-08-23_19-05-00_8362.dat',
        directory / 'Biomet_2019-08-23_19-05-00_8362.dat',
    )

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.finseflux_Biomet]
path = "{directory}"
pattern = "Biomet_*.dat"
pipeline = "archive_first"
''')

    assert call_command('file_archive', config, skip=0) == 0
    obj = ImportFile.objects.get()
    assert obj.status == ImportFile.Status.PENDING

    # Import the archived file into ClickHouse
    assert call_command('file_import', config) == 0
    obj.refresh_from_db()
    assert obj.status == ImportFile.Status.DONE

    response = api_user.query_ch('finseflux_Biomet')
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 288
    # Every row carries the archive path of its source file, the same
    # archive-relative path used by the wsn_importfile ledger
    index = json['columns'].index('source_file')
    assert all(row[index] == obj.path for row in json['rows'])

    # The table is partitioned by month
    with ClickHouse() as clickhouse:
        partition_key = clickhouse.execute(
            "SELECT partition_key FROM system.tables "
            f"WHERE database = '{settings.CLICKHOUSE_NAME}' "
            "AND name = 'finseflux_Biomet'")
    assert partition_key == [('toYYYYMM(toDateTime(TIMESTAMP))',)]


def test_file_register(db, tmp_path):
    directory = tmp_path / 'data'
    (directory / 'archive' / '2019' / '05').mkdir(parents=True)
    (directory / 'archive' / '2020' / '01').mkdir(parents=True)
    # A CR6 and a Licor archive
    (directory / 'archive' / '2019' / '05' / 'Biomet_2019-05-01_00-00-00_1.dat.xz').touch()
    (directory / 'archive' / '2020' / '01' / '2018-05-07T160000_Flux.tar.xz').touch()
    # Unknown suffix, gets no row
    (directory / 'archive' / '2020' / '01' / 'notes.bin.xz').touch()

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.test]
path = "{directory}"
pattern = "*.dat"
pipeline = "archive_first"

[import.old_entry]
path = "{directory}"
pattern = "*.dat"
''')

    assert call_command('file_register', config) == 0
    assert ImportFile.objects.count() == 2
    assert ImportFile.objects.filter(name='test').count() == 2

    # Idempotent
    assert call_command('file_register', config) == 0
    assert ImportFile.objects.count() == 2


def test_file_register_import(api_user, db, tmp_path):
    # Simulate the migration of a logger from the old pipeline: files have
    # been archived without rows, file_register completes the ledger and
    # file_import imports the data.
    directory = tmp_path / 'eton2'
    directory.mkdir(parents=True)
    for path in ETON2.iterdir():
        shutil.copy(path, directory / path.name)

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.eton2]
path = "{directory}"
pattern = "*.dat"
database = "postgres"
pipeline = "archive_first"
''')

    # The old pipeline archives files without registering them
    for path in directory.iterdir():
        parser = CR6Parser(path)
        parser.parse()
        parser.archive()
    assert ImportFile.objects.count() == 0

    assert call_command('file_register', config) == 0
    assert ImportFile.objects.count() == len(list(ETON2.iterdir()))
    assert ImportFile.objects.filter(status=ImportFile.Status.PENDING).count() == len(list(ETON2.iterdir()))

    assert call_command('file_import', config) == 0
    response = api_user.query_pg()
    assert len(response.json()['rows']) == 168
    assert ImportFile.objects.filter(status=ImportFile.Status.DONE).count() == len(list(ETON2.iterdir()))


def test_file_register_lock(tmp_path):
    # A second file_register run must fail loudly while another one holds
    # the lock (e.g. overlapping cron jobs).
    lockpath = settings.BASE_DIR / 'var' / 'run' / 'file_register.lock'
    lockpath.parent.mkdir(parents=True, exist_ok=True)
    config = tmp_path / 'config.toml'
    config.write_text('[import]\n')

    with open(lockpath, 'w') as lockfile:
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(CommandError, match='another file_register run'):
            call_command('file_register', config)


@requires_clickhouse
def test_import_finseflux(api_user, clickhouse, datadir):
    path = datadir / 'cr6' / 'finseflux'
    files = list(path.iterdir())

    config = datadir / 'config.toml'
    name = 'finseflux_Biomet'

    # Test skipping files
    skip = int(time.time() - datetime.datetime(2018, 1, 1).timestamp()) // 60
    assert call_command('import_file', config, name=name, skip=skip) == 0

    # Test importing data
    assert call_command('import_file', config, name=name, skip=0) == 0

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

    # Verify the files have been archived (empty files are deleted)
    prefix = 'Biomet_'
    for path in files:
        if path.name.startswith(prefix):
            assert not path.exists()
            if path.name.endswith('_empty.dat'):
                continue
            assert (
                is_archived(path) or
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
    assert call_command('import_file', config, name=name, skip=skip) == 0

    # Test importing data
    assert call_command('import_file', config, name=name, skip=0) == 0
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
                is_archived(path) or
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
    assert call_command('import_file', config, name=name, skip=skip) == 0

    # Test importing data
    assert call_command('import_file', config, name=name, skip=0) == 0
    # Verify the data has been imported
    response = api_user.query_ch(name)
    assert response.status_code == 200
    json = response.json()
    assert len(json['rows']) == 30

    # Verify the files have been archived
    for path in files:
        assert not path.exists()
        assert (
            is_archived(path) or
            Path(f'{path}.truncated').exists()
        )


def test_archive_migrate(tmp_path):
    directory = tmp_path / 'cr6' / 'finseflux'
    directory.mkdir(parents=True)
    (directory / '2018').mkdir()
    (directory / 'archive' / '2019' / '01').mkdir(parents=True)

    # A flat archived file at the root
    root_file = directory / 'Biomet_2018-02-09_12-35-00_0.dat.xz'
    root_file.touch()
    # An archived file in a manually created year directory
    year_file = directory / '2018' / 'Biomet_2018-03-01_10-00-00_1.dat.xz'
    year_file.touch()
    # Already migrated, must be left alone
    done_file = directory / 'archive' / '2019' / '01' / 'Biomet_2019-01-05_01-00-00_2.dat.xz'
    done_file.touch()
    # No date in the filename, must be reported and skipped
    undated = directory / 'UIO_Constants_Eton2_1.dat.xz'
    undated.touch()
    # Sommer filename with a 2-digit year, handled by SommerParser
    sommer_file = directory / '17170060_19-12-11T12-01-49.csv.xz'
    sommer_file.touch()
    # 0-byte .empty leftover, must be removed
    quarantined = directory / 'Biomet_2026-09-23_10-15-00_5.dat.empty'
    quarantined.touch()
    # Non-empty .empty file, must be kept
    not_empty = directory / 'Biomet_2026-09-23_10-15-00_6.dat.empty'
    not_empty.write_text('oops')
    input_file = directory / 'Biomet_2026-09-24_10-15-00_6.dat'
    input_file.touch()

    config = tmp_path / 'config.toml'
    config.write_text(f'''
[import]

[import.finseflux_Biomet]
path = "{directory}"
pattern = "Biomet_*.dat"
''')

    # Dry run: nothing moves
    call_command('archive_migrate', config)
    assert root_file.exists()
    assert year_file.exists()
    assert sommer_file.exists()
    assert quarantined.exists()

    call_command('archive_migrate', config, apply=True)

    assert not root_file.exists()
    assert (directory / 'archive' / '2018' / '02' / root_file.name).exists()

    assert not year_file.exists()
    assert (directory / 'archive' / '2018' / '03' / year_file.name).exists()
    # The emptied year directory has been removed
    assert not (directory / '2018').exists()

    # The Sommer file is dated via SommerParser.get_archive_date()
    assert not sommer_file.exists()
    assert (directory / 'archive' / '2019' / '12' / sommer_file.name).exists()

    assert done_file.exists()
    assert undated.exists()
    assert not quarantined.exists()
    assert not_empty.exists()
    assert input_file.exists()
