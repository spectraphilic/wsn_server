import csv
import datetime
import logging
import math
import sys


logger = logging.getLogger(__name__)


class CR6Parser:
    """
    Campbell CR6.
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self.file = None

    def __enter__(self):
        self.file = open(self.filepath)
        try:
            self.parse()
        except Exception:
            self.__exit__(None, None, None)
            raise

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.file.close()

    def parse(self):
        self.reader = csv.reader(self.file)
        env = self.reader.__next__()
        assert len(env) == 8
        assert env[0] == 'TOA5'
        self.tags = {
            'name': env[1],                # mobileflux1
            'model': env[2],               # CR6
            'serial': int(env[3]),         # 744
            'os_version': env[4],          # CR6.Std.07
            'prog_name': env[5],           # CPU:flux_stations.CR6
            'prog_signature': int(env[6]), # 55208
            'table_name': env[7],          # Biomet
        }

        self.fields = self.reader.__next__()
        self.units = self.reader.__next__()
        self.reader.__next__() # abbreviations

    def __convert(self, value, unit):
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

    def __iter__(self):
        # FIXME Should reject a line if it doesn't have an end-of-line, because
        # then the last value is probably truncated.  Better to reject the
        # whole line than to import a bad value, right?
        # But the csv module has already stripped the end-of-line, so we cannot
        # know.
        for row in self.reader:
            data = {}
            for i, value in enumerate(row):
                name = self.fields[i]
                try:
                    value = self.__convert(value, self.units[i])
                except Exception:
                    lineno = self.reader.line_num
                    logger.exception(
                        f'error in file {self.filepath} at row {lineno} column {i}'
                    )
                    break

                if name == 'TIMESTAMP':
                    time = value
                else:
                    data[name] = value
            else:
                yield (time, data)


# For trying purposes
if __name__ == '__main__':
    filepath = sys.argv[1]
    with CR6Parser(filepath) as parser:
        print(parser.fields)
