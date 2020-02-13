# Standard Library
import csv
import datetime
import logging
import math
import os

# Project
from wsn.parsers.base import CSVParser
from wsn.parsers.base import EmptyError, TruncatedError


logger = logging.getLogger(__name__)

class SommerParser(CSVParser):
    """
    Sommer MRL-7
    """

    OPEN_KWARGS = {'newline': '', 'encoding': 'utf-8-sig'}

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
        if value == '':
            return math.nan

        for t in int, float:
            try:
                return t(value)
            except ValueError:
                pass

        return value

    def _parse_time(self, data):
        value = data.pop('TIMESTAMP') # 2019-12-11 11:32:00
        time = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        time = time.replace(tzinfo=datetime.timezone.utc)
        return time, data
