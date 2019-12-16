# Standard Library
import csv
import datetime
import math
import sys

# Project
from wsn.parsers.base import CSVParser


class EddyproParser(CSVParser):

    def _parse_header(self):
        self.reader = csv.reader(self.file)

        # Skip header rows. The fields row must have a date and time columns.
        line = self.reader.__next__()
        while 'date' not in line or 'time' not in line:
            line = self.reader.__next__()

        self.fields = line
        self.units = self.reader.__next__()

    def _parse_value(self, name, unit, value):
        if value == 'NaN':
            return math.nan

        for t in int, float:
            try:
                return t(value)
            except ValueError:
                pass

        return value

    def _parse_time(self, data):
        date = data.pop('date')
        time = data.pop('time')
        time = datetime.datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        time = time.replace(tzinfo=datetime.timezone.utc)
        return time, data


# For trying purposes
if __name__ == '__main__':
    filepath = sys.argv[1]
    parser = EddyproParser()
    metadata, fields, rows = parser.parse(filepath)
    print(metadata)
    print(fields)
    for time, data in rows:
        print(time)
        print(data)
        break
