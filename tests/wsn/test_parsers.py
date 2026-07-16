from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile

# Requirements
import pytest

# Project
from wsn.parsers.base import EmptyError, TruncatedError
from wsn.parsers.cr6 import CR6Parser
from wsn.parsers.eddypro import EddyproParser
from wsn.parsers.licor import LicorParser
from wsn.parsers.schemas import Schema
from wsn.parsers.sommer import SommerParser


@pytest.fixture(scope='module')
def datadir():
    return Path('tests/data')


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
        assert type(time) is datetime and time.tzinfo == timezone.utc
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
    assert time == datetime(2026, 6, 23, 10, 43, 18, 200000, tzinfo=timezone.utc)
    assert data['Ux'] == 0.96
    assert data['Uy'] == 0.03
    assert data['Uz'] == 0.1
    assert data['Ts'] == 20.28

    time, data = rows[1]
    assert time == datetime(2026, 6, 23, 10, 43, 18, 250000, tzinfo=timezone.utc)
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
        assert type(time) is datetime and time.tzinfo == timezone.utc
        assert type(data) is dict
        assert fields == set(data)


def test_eddypro():
    filename = 'tests/data/eddypro/eddypro_0_full_output_2019-08-26T155701_adv.csv'

    parser = EddyproParser(filename)
    metadata, fields, rows = parser.parse()
    assert type(metadata) is dict
    assert type(fields) is list
    assert type(rows) is list
    assert len(rows) == 3

    fields = set(fields)
    fields.remove('date')
    fields.remove('time')
    for time, data in rows:
        assert type(time) is datetime and time.tzinfo == timezone.utc
        assert type(data) is dict
        assert fields == set(data)


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
        assert type(time) is datetime and time.tzinfo == timezone.utc
        assert type(data) is dict
        assert fields == set(data)
