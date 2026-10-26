from datetime import UTC, date, datetime
from pathlib import Path
from zipfile import BadZipFile, ZipFile
import shutil

# Requirements
import pytest

# Project
from wsn.parsers import get_parser
from wsn.parsers.base import (
    EmptyError,
    TruncatedError,
    check_row_time,
    parse_filename_date,
    unarchive,
    validate_rows,
)
from wsn.parsers.cr6 import CR6Parser
from wsn.parsers.licor import LicorParser
from wsn.parsers.schemas import Schema
from wsn.parsers.sommer import SommerParser


@pytest.fixture(scope='module')
def datadir():
    return Path('tests/data')


def test_parse_filename_date():
    assert parse_filename_date('HFData_2026-07-01_01-00-00_639.dat') == date(2026, 7, 1)
    assert parse_filename_date('uio_data_cr1000_2016_11_25_0000.dat') == date(2016, 11, 25)
    assert parse_filename_date('2018-05-07T160000_LATICE-Flux_Finse.ghg') == date(2018, 5, 7)
    assert parse_filename_date('Biomet_2019-08-23_19-05-00_8362.dat.xz') == date(2019, 8, 23)

    # Sommer filenames have a 2-digit year, no 4-digit date
    with pytest.raises(ValueError):
        parse_filename_date('17170060_19-12-11T12-01-49.csv')

    # Invalid dates are rejected
    with pytest.raises(ValueError):
        parse_filename_date('HFData_2026-13-01_01-00-00_639.dat')
    with pytest.raises(ValueError):
        parse_filename_date('HFData_2026-02-30_01-00-00_639.dat')

    with pytest.raises(ValueError):
        parse_filename_date('no_date_here.dat')


def test_check_row_time():
    filename_date = date(2019, 5, 20)

    # Real rows: from the start of the project until a little after the
    # filename date (a file accumulates rows until the logger rotates it)
    assert check_row_time(datetime(2015, 1, 1, tzinfo=UTC), filename_date) is None
    assert check_row_time(datetime(2019, 5, 20, 13, tzinfo=UTC), filename_date) is None
    assert check_row_time(datetime(2019, 7, 19, tzinfo=UTC), filename_date) is None

    # More than 60 days after the filename date means the clock is wrong
    assert check_row_time(datetime(2019, 7, 20, tzinfo=UTC), filename_date) is not None
    assert check_row_time(datetime(2028, 1, 1, tzinfo=UTC), filename_date) is not None

    # Before the start of the project means the clock is wrong
    assert check_row_time(datetime(2014, 12, 31, 23, 59, 59, tzinfo=UTC), filename_date) is not None
    assert check_row_time(datetime(1999, 1, 1, tzinfo=UTC), filename_date) is not None
    assert check_row_time(datetime(2001, 1, 1, tzinfo=UTC), filename_date) is not None

    # Epoch is accepted
    epoch = int(datetime(2019, 5, 20, 13, tzinfo=UTC).timestamp())
    assert check_row_time(epoch, filename_date) is None

    # Broken timestamps
    assert check_row_time(None, filename_date) is not None
    assert check_row_time(datetime(2019, 5, 20), filename_date) is not None
    assert check_row_time('2019-05-20', filename_date) is not None


def test_validate_rows():
    rows = [
        (datetime(2019, 5, 20, 13, tzinfo=UTC), {'a': 1}),
        (datetime(2019, 7, 19, tzinfo=UTC), {'a': 4}),  # 60 days after
        (datetime(2001, 1, 1, tzinfo=UTC), {'a': 2}),
        (datetime(2028, 1, 1, tzinfo=UTC), {'a': 5}),
        (None, {'a': 3}),
    ]
    good, bad = validate_rows(rows, 'uio_data_cr6_2019_05_20_1300.dat')

    assert good == rows[:2]
    assert bad[0][2] == 'timestamp 2001-01-01 00:00:00+00:00 is before 2015-01-01'
    assert bad[1][2] == ('timestamp 2028-01-01 is more than 60 days '
                         'after the filename date 2019-05-20')
    assert bad[2][2] == 'no timestamp'

    # Archived licor files keep a .tar.xz suffix
    good, bad = validate_rows(rows, '2019-05-20T130000_X.tar.xz')
    assert good == rows[:2]
    assert len(bad) == 3

    # No date in the filename
    with pytest.raises(ValueError):
        validate_rows(rows, 'uio_data_cr6.dat.xz')


def test_cr6_empty(datadir):
    filename = str(datadir / 'cr6' / 'finseflux' / 'Biomet_2019-08-23_19-05-00_8362_empty.dat')

    parser = CR6Parser(filename)
    with pytest.raises(EmptyError):
        parser.parse()

    with open(filename) as f:
        parser = CR6Parser(f)
        with pytest.raises(EmptyError):
            parser.parse()


def test_cr6_truncated(datadir):
    filename = str(datadir / 'cr6' / 'finseflux' / 'Biomet_2019-08-23_19-05-00_8362_truncated.dat')

    parser = CR6Parser(filename)
    with pytest.raises(TruncatedError):
        parser.parse()

    with open(filename) as f:
        parser = CR6Parser(f)
        with pytest.raises(TruncatedError):
            parser.parse()


def test_cr6(datadir):
    filename = str(datadir / 'cr6' / 'finseflux' / 'Biomet_2019-08-23_19-05-00_8362.dat')

    parser = CR6Parser(filename)
    metadata, fields, rows = parser.parse()
    assert type(metadata) is dict
    assert type(fields) is list
    assert type(rows) is list
    assert len(rows) == 288

    fields = set(fields)
    fields.remove('TIMESTAMP')
    for time, data in rows:
        assert type(time) is datetime and time.tzinfo == UTC
        assert type(data) is dict
        assert fields == set(data)


def test_cr6_myr1_sonic_mapping(tmp_path):
    """CR6 myr1 sonic columns WC1/WC2/WC3/C map to Ux/Uy/Uz/Ts."""
    content = (
        '"TOA5","54833","CR1000X","54833","CR1000X.8.3.0","CPU:Hisasen1_test.CR1X","21544","HFData"\r\n'
        '"TIMESTAMP","RECORD","HS50_NBytesReturned","WC1","WC2","WC3","C","CO2_dry","H2O_dry"\r\n'
        '"TS","RN","","m/S","m/S","m/S","°C","umol/mol","mmol/mol"\r\n'
        '"","","Smp","Smp","Smp","Smp","Smp","Smp","Smp"\r\n'
        '"2026-06-23 10:43:18.2",0,"36",0.96,0.03,0.1,20.28,413.3152,7.916359\r\n'
        '"2026-06-23 10:43:18.25",1,"36",0.97,0.13,0.06,20.76,412.9817,7.969986\r\n'
    )
    filepath = tmp_path / 'HFData_2026-06-23_10-43-18_0.dat'
    filepath.write_text(content, newline='')

    parser = CR6Parser(filepath, schema=Schema('cr6_myr1_sonic', strict=True))
    metadata, fields, rows = parser.parse()

    assert set(fields) == {'TIMESTAMP', 'Ux', 'Uy', 'Uz', 'Ts'}
    assert len(rows) == 2

    time, data = rows[0]
    assert time == datetime(2026, 6, 23, 10, 43, 18, 200000, tzinfo=UTC)
    assert data['Ux'] == 0.96
    assert data['Uy'] == 0.03
    assert data['Uz'] == 0.1
    assert data['Ts'] == 20.28

    time, data = rows[1]
    assert time == datetime(2026, 6, 23, 10, 43, 18, 250000, tzinfo=UTC)
    assert data['Ux'] == 0.97
    assert data['Uy'] == 0.13
    assert data['Uz'] == 0.06
    assert data['Ts'] == 20.76


def test_licor_empty():
    filename = 'tests/data/licor/raw/2018-05-07T160000_LATICE-Flux_Finse_empty.ghg'

    parser = LicorParser(filename)
    with pytest.raises(BadZipFile):
        parser.parse()

    with open(filename) as f:
        parser = LicorParser(f)
        with pytest.raises(BadZipFile):
            parser.parse()


def test_licor():
    filename = 'tests/data/licor/raw/2018-05-07T160000_LATICE-Flux_Finse.ghg'

    parser = LicorParser(filename)
    metadata, fields, rows = parser.parse()
    assert type(metadata) is dict
    assert type(fields) is list
    assert type(rows) is list
    assert len(rows) == 18000

    fields = set(fields)
    fields.remove('TIMESTAMP')
    for time, data in rows:
        assert type(time) is datetime and time.tzinfo == UTC
        assert type(data) is dict
        assert fields == set(data)


def test_licor_ch4(tmp_path):
    # A methane analyzer will be installed at Finse; its .ghg files carry
    # CH4 columns, which the licor_finseflux schema must map. The sample
    # file predates the analyzer, so copy it and add the columns
    src = Path('tests/data/licor/raw/2018-05-07T160000_LATICE-Flux_Finse.ghg')
    dst = tmp_path / src.name

    ch4_fields = ['CH4 (mmol/m^3)', 'CH4 (umol/mol)', 'CH4 Temperature',
                  'CH4 Pressure', 'CH4 Signal Strength']
    ch4_values = ['1.9', '1900.5', '25.1', '99.2', '62.0']
    with ZipFile(src) as zin, ZipFile(dst, 'w') as zout:
        for name in zin.namelist():
            data = zin.read(name)
            if name.endswith('.data') and not name.endswith('-biomet.data'):
                lines = data.decode().splitlines(keepends=True)
                for i, line in enumerate(lines):
                    if line.startswith('DATAH\t'):
                        lines[i] = line.rstrip('\r\n') + '\t' + '\t'.join(ch4_fields) + '\n'
                    elif line.startswith('DATA\t'):
                        lines[i] = line.rstrip('\r\n') + '\t' + '\t'.join(ch4_values) + '\n'
                data = ''.join(lines).encode()
            zout.writestr(name, data)

    schema = Schema('licor_finseflux', strict=True)
    parser = LicorParser(str(dst), schema=schema)
    metadata, fields, rows = parser.parse()

    for name in ['CH4_mmol_m3', 'CH4_umol_mol', 'CH4_Temperature',
                 'CH4_Pressure', 'CH4_Signal_Strength']:
        assert name in fields
    time, data = rows[0]
    assert data['CH4_mmol_m3'] == 1.9
    assert data['CH4_umol_mol'] == 1900.5
    assert data['CH4_Temperature'] == 25.1
    assert data['CH4_Pressure'] == 99.2
    assert data['CH4_Signal_Strength'] == 62.0

    # Old files have no CH4 columns and still parse as before
    schema = Schema('licor_finseflux', strict=True)
    parser = LicorParser(str(src), schema=schema)
    metadata, fields, rows = parser.parse()
    assert not any(name.startswith('CH4') for name in fields)


def test_get_parser():
    assert get_parser('HFData_2025-06-10_15-10-00_2894.dat.xz') is CR6Parser
    assert get_parser('17170060_19-12-11T12-01-49.csv.xz') is SommerParser
    # Only Licor archives as tar.xz, and without the .ghg suffix
    assert get_parser('2018-05-07T160000_LATICE-Flux_Finse.tar.xz') is LicorParser
    assert get_parser('whatever.bin.xz') is None


def test_licor_archive_round_trip(tmp_path):
    # Archiving a .ghg file converts it to .ghg.tar.xz (LicorParser.archive);
    # unarchive() must restore a file that parses identically, this is the
    # path file_import relies on.
    name = '2018-05-07T160000_LATICE-Flux_Finse.ghg'
    ghg = tmp_path / name
    shutil.copy(f'tests/data/licor/raw/{name}', ghg)

    parser = LicorParser(ghg)
    metadata1, fields1, rows1 = parser.parse()

    # Archive: the source is removed, a .tar.xz is created under archive/,
    # e.g. 'X.ghg' is archived as 'X.tar.xz'
    relpath = LicorParser.get_archive_relpath(ghg)
    assert relpath == Path('2018/05') / f'{name.removesuffix(".ghg")}.tar.xz'
    dst = parser.archive()
    assert not ghg.exists()
    assert dst == tmp_path / 'archive' / relpath

    # Unarchive and parse again: identical result
    out = tmp_path / 'restored'
    out.mkdir()
    ghg2 = unarchive(dst, out)
    assert ghg2.name == name
    metadata2, fields2, rows2 = LicorParser(ghg2).parse()

    assert metadata2 == metadata1
    assert fields2 == fields1
    assert rows2 == rows1


def test_sommer_archive_date():
    # Filenames use a 2-digit year, e.g. 17170060_19-12-11T12-01-49.csv
    assert SommerParser.get_archive_date('17170060_19-12-11T12-01-49.csv') == date(2019, 12, 11)
    # A non-Sommer .csv file still uses the strict 4-digit date
    assert SommerParser.get_archive_date('Diagnostic_2023-09-14_00-05-00_0.csv') == date(2023, 9, 14)
    with pytest.raises(ValueError):
        SommerParser.get_archive_date('no_date_here.csv')


def test_sommer():
    filename = 'tests/data/sommer/17170060_19-12-11T12-01-49.csv'

    parser = SommerParser(filename)
    metadata, fields, rows = parser.parse()
    assert type(metadata) is dict
    assert type(fields) is list
    assert type(rows) is list
    assert len(rows) == 30

    fields = set(fields)
    fields.remove('TIMESTAMP')
    for time, data in rows:
        assert type(time) is datetime and time.tzinfo == UTC
        assert type(data) is dict
        assert fields == set(data)
