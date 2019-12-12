from datetime import datetime
from zipfile import BadZipFile

import pytest

from wsn.parsers.base import EmptyError, TruncatedError
from wsn.parsers.cr6 import CR6Parser
from wsn.parsers.eddypro import EddyproParser
from wsn.parsers.licor import LicorParser


def test_cr6_empty():
    filename = 'tests/data/Biomet_2019-08-23_19-05-00_8362_empty.dat'

    parser = CR6Parser(filename)
    with pytest.raises(EmptyError):
        parser.parse()

    with open(filename) as f:
        parser = CR6Parser(f)
        with pytest.raises(EmptyError):
            parser.parse()


def test_cr6_truncated():
    filename = 'tests/data/Biomet_2019-08-23_19-05-00_8362_truncated.dat'

    parser = CR6Parser(filename)
    with pytest.raises(TruncatedError):
        parser.parse()

    with open(filename) as f:
        parser = CR6Parser(f)
        with pytest.raises(TruncatedError):
            parser.parse()


def test_cr6():
    filename = 'tests/data/Biomet_2019-08-23_19-05-00_8362.dat'

    parser = CR6Parser(filename)
    metadata, fields, rows = parser.parse()
    assert type(metadata) is dict
    assert type(fields) is list
    assert type(rows) is list
    assert len(rows) == 288

    fields = set(fields)
    fields.remove('TIMESTAMP')
    for time, data in rows:
        assert type(time) is datetime
        assert type(data) is dict
        assert fields == set(data)


def test_licor_empty():
    filename = 'tests/data/2018-05-07T160000_LATICE-Flux_Finse_empty.ghg'

    parser = LicorParser(filename)
    with pytest.raises(BadZipFile):
        parser.parse()

    with open(filename) as f:
        parser = LicorParser(f)
        with pytest.raises(BadZipFile):
            parser.parse()


def test_licor():
    filename = 'tests/data/2018-05-07T160000_LATICE-Flux_Finse.ghg'

    parser = LicorParser(filename)
    metadata, fields, rows = parser.parse()
    assert type(metadata) is dict
    assert type(fields) is list
    assert type(rows) is list
    assert len(rows) == 18000

    fields = set(fields)
    fields.remove('Seconds')
    fields.remove('Nanoseconds')
    fields.remove('Date')
    fields.remove('Time')
    for time, data in rows:
        assert type(time) is datetime
        assert type(data) is dict
        assert fields == set(data)


def test_eddypro():
    filename = 'tests/data/eddypro_0_full_output_2019-08-26T155701_adv.csv'

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
        assert type(time) is datetime
        assert type(data) is dict
        assert fields == set(data)
