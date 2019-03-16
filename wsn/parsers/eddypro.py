import csv
import datetime
import math
import sys

from .base import CSVParser


class EddyproParser(CSVParser):

    @property
    def metadata(self):
        return {}

    def parse_header(self):
        self.reader = csv.reader(self.file)

        self.reader.__next__() # Skip 1st line
        self.fields = self.reader.__next__()
        self.units = self.reader.__next__()

    def parse_value(self, name, unit, value):
        if value == 'NaN':
            return math.nan

        for t in int, float:
            try:
                return t(value)
            except ValueError:
                pass

        return value

    def parse_time(self, data):
        date = data.pop('date')
        time = data.pop('time')
        time = datetime.datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        time = time.replace(tzinfo=datetime.timezone.utc)
        return time, data


# For trying purposes
if __name__ == '__main__':
    filepath = sys.argv[1]
    with EddyproParser(filepath) as parser:
        print(parser.metadata)
        for time, data in parser:
            print(time)
            print(data)
            print()
