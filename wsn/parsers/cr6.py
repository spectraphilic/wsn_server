# Standard Library
import csv
import datetime
import logging
import math
import os
import sys

# App
from .base import CSVParser


logger = logging.getLogger(__name__)


class CR6Parser(CSVParser):
    """
    Campbell CR6.
    """

    def parse_header(self):
        # 1st verify the file is not trunctated (it may still be truncated
        # right after the end of a row, that we cannot know)
        # This method works for text files.
        f = self.file
        f.seek(0, os.SEEK_END)
        n = f.tell()
        assert n > 1 # not empty
        f.seek(n - 2, os.SEEK_SET)
        assert f.read(2) == '\r\n' # ends with a newline
        f.seek(0) # back to the beginning

        # Parse first line
        self.reader = csv.reader(self.file)
        self.env = self.reader.__next__()
        assert len(self.env) == 8
        assert self.env[0] == 'TOA5'

        self.fields = self.reader.__next__()
        self.units = self.reader.__next__()
        self.reader.__next__() # abbreviations

    @property
    def metadata(self):
        env = self.env
        return {
            'name': env[1],                # mobileflux1
            'model': env[2],               # CR6
            'serial': int(env[3]),         # 744
            'os_version': env[4],          # CR6.Std.07
            'prog_name': env[5],           # CPU:flux_stations.CR6
            'prog_signature': int(env[6]), # 55208
            'table_name': env[7],          # Biomet
        }

    def parse_value(self, name, unit, value):
        assert value, 'unexpected empty string'

        if unit == 'TS':
            value = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return value.replace(tzinfo=datetime.timezone.utc)

        if value == 'NAN':
            return math.nan

        try:
            return int(value)
        except ValueError:
            return float(value)

    def parse_time(self, data):
        time = data.pop('TIMESTAMP')
        return time, data


# For trying purposes
if __name__ == '__main__':
    filepath = sys.argv[1]
    with CR6Parser(filepath) as parser:
        print(parser.metadata)
        for time, data in parser:
            print(time)
            print(data)
            break
