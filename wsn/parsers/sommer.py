# Standard Library
import csv
import datetime
import logging
import math
import os
import re

# Project
from wsn.parsers.base import CSVParser
from wsn.parsers.base import EmptyError, TruncatedError, parse_filename_date


logger = logging.getLogger(__name__)

DATE_RE = re.compile(r'(?<![\d-])(\d{2})-(\d{2})-(\d{2})T')

class SommerParser(CSVParser):
    """
    Sommer MRL-7
    """

    OPEN_KWARGS = {'newline': '', 'encoding': 'utf-8-sig'}

    @staticmethod
    def get_archive_date(name):
        # Sommer filenames use a 2-digit year, e.g. 17170060_19-12-11T12-01-49.csv,
        # but the file may not come from a Sommer sensor at all (the mapping is
        # by suffix), so try the strict default first
        try:
            return parse_filename_date(name)
        except ValueError:
            match = DATE_RE.search(name)
            if match is None:
                raise ValueError(f'no date found in filename: {name}')
            return datetime.date(2000 + int(match[1]), int(match[2]), int(match[3]))

    def _open(self):
        if self.size == 0:
            raise EmptyError()

        # 1st verify the file is not trunctated (it may still be truncated
        # right after the end of a row, that we cannot know)
        # This method works for text files.
        f = self.file
        f.seek(self.size - 2, os.SEEK_SET)
        if f.read(2) != '\r\n':
            raise TruncatedError()

        f.seek(0) # back to the beginning

    def _parse_header(self):
        self.reader = csv.reader(self.file, delimiter=';')

        line = self.reader.__next__()
        assert line[0] == 'SommerXF'

        # Header signature
        line = self.reader.__next__()
        assert line[0] == 'HSG'

        # Station ID
        line = self.reader.__next__()
        assert line[0] == 'SID'
        #station_id = line[1]
        #station_name = line[2]

        # Channel position
        line = self.reader.__next__()
        assert line[0] == 'CP' and line[1] == ''

        # Channel name
        line = self.reader.__next__()
        assert line[0] == 'CL' and line[1] == ''
        self.fields = ['TIMESTAMP'] + line[2:]

        # Channel unit
        line = self.reader.__next__()
        assert line[0] == 'CU' and line[1] == ''
        self.units = line[1:]

    def _parse_row(self, row):
        first = row[0]
        if first == 'D':
            return super()._parse_row(row[1:])
        elif first == 'A':
            raise NotImplementedError('Asynchronous (A) data lines not yet supported')
        elif first == 'SIG':
            return None # XXX Nothing else shuld be parsed from here
        else:
            logger.warning(f'Unexpected data line "{first}"')
            return None

    def _parse_value(self, name, unit, value):
        if name == 'TIMESTAMP':
            return value

        if value == '':
            return math.nan

        try:
            return int(value)
        except ValueError:
            pass

        value = value.replace(',', '.')
        return float(value)

    def _parse_time(self, data):
        value = data.pop('TIMESTAMP') # 2019-12-11 11:32:00
        time = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        time = time.replace(tzinfo=datetime.timezone.utc)
        return time, data
