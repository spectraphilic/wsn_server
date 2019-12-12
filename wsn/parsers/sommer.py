# Standard Library
import csv
import datetime

# Project
from wsn.parsers.base import CSVParser


class SommerParser(CSVParser):

    @property
    def metadata(self):
        return {}

    def _parse_header(self):
        self.reader = csv.reader(self.file, delimiter=';')

        line = self.reader.__next__()
        line = self.reader.__next__()
        assert line[0] == 'HSG'
        line = self.reader.__next__()
        assert line[0] == 'SID'
        line = self.reader.__next__()
        assert line[0] == 'CP' and line[1] == ''

        line = self.reader.__next__()
        assert line[0] == 'CL' and line[1] == ''
        self.fields = line[1:]

        line = self.reader.__next__()
        assert line[0] == 'CU' and line[1] == ''
        self.units = line[1:]

    def _parse_row(self, row):
        first = row[0]
        if first == 'D':
            data = super()._parse_row(row[1:])
            return data
        elif first == 'SIG':
            return None
        else:
            raise ValueError(f'Unexpected row "{first}"')

    def _parse_value(self, name, unit, value):
        for t in int, float:
            try:
                return t(value)
            except ValueError:
                pass

        return value

    def _parse_time(self, data):
        value = data.pop('') # 2019-12-11 11:32:00
        time = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        time = time.replace(tzinfo=datetime.timezone.utc)
        return time, data
