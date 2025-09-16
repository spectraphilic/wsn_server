import csv
import datetime
import math
import os
import sys

# Project
from wsn.parsers.base import CSVParser
from wsn.parsers.base import EmptyError, TruncatedError



def parse_datetime(value):
    formats = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']
    for fmt in formats:
        try:
            value = datetime.datetime.strptime(value, fmt)
            return value.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            pass
    else:
        raise ValueError(f'Failed to parse "{value}" timestamp')


class CR6Parser(CSVParser):
    """
    Campbell CR6.
    """

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
        # Parse first line
        self.reader = csv.reader(self.file)
        self.env = self.reader.__next__()
        assert len(self.env) == 8
        assert self.env[0] == 'TOA5'

        self.fields = self.reader.__next__()
        self.units = self.reader.__next__()
        self.reader.__next__() # abbreviations

        env = self.env
        try:
            serial = int(env[3])
        except ValueError:
            serial = env[3]
        self.metadata = {
            'name': env[1],                # mobileflux1
            'model': env[2],               # CR6
            'serial': serial,              # 744
            'os_version': env[4],          # CR6.Std.07
            'prog_name': env[5],           # CPU:flux_stations.CR6
            'prog_signature': int(env[6]), # 55208
            'table_name': env[7],          # Biomet
        }

    def _parse_value(self, name, unit, value):
        if unit == 'TS':
            return parse_datetime(value)

        # Found "-" in the U_ana column of a HFData file
        if unit == 'm/S':
            try:
                return float(value)
            except ValueError:
                return math.nan

        if value == 'NAN':
            return math.nan

        types = [int, float, str]
        for t in types:
            try:
                return t(value)
            except ValueError:
                pass

    def _parse_time(self, data):
        time = data.pop('TIMESTAMP')
        return time, data


# For trying purposes
if __name__ == '__main__':
    filepath = sys.argv[1]
    parser = CR6Parser(filepath)
    metadata, fields, rows = parser.parse()
    print(metadata)
    print(fields)
    for time, data in rows:
        print(time)
        print(data)
        break
