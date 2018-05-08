import configparser
import csv
import datetime
import io
import os
import sys
from zipfile import ZipFile


class DataFile:
    def __init__(self, parser):
        self.file = None
        self.parser = parser
        self.reader = None
        self.header = {}
        self.fields = []

    def open(self, filename):
        self.file = io.TextIOWrapper(self.parser.file.open(filename))
        self.parse()

    def close(self):
        self.file.close()

    def parse(self):
        self.reader = csv.reader(self.file, dialect='excel-tab')
        # Read Header
        for row in self.reader:
            if len(row) != 2:
                self.fields = row
                break
            self.header[row[0]] = row[1]

    def __convert(self, value):
        try:
            return int(value) # integer
        except ValueError:
            pass

        try:
            return float(value) # float
        except ValueError:
            return value # text

    def __iter__(self):
        skip = {'DATE', 'TIME', 'Seconds', 'Nanoseconds', 'Date', 'Time'}

        if 'DATE' in self.fields:
            i_date = self.fields.index('DATE')
            i_time = self.fields.index('TIME')
        else:
            i_date = self.fields.index('Date')
            i_time = self.fields.index('Time')

        def get_time(row):
            date = row[i_date]
            time, ms = row[i_time].rsplit(':', 1)
            dt = datetime.datetime.strptime(date + time, '%Y-%m-%d%H:%M:%S')
            dt = dt.replace(microsecond=int(ms)*1000)
            # TODO Assert it matches Seconds/Nanoseconds
            return dt

        for row in self.reader:
            time = get_time(row)
            data = {}
            for i, value in enumerate(row):
                name = self.fields[i]
                if name not in skip:
                    data[name] = self.__convert(value)

            yield (time, data)


class LicorParser:
    """
    Licor.

    https://www.licor.com/env/help/eddypro/topics_eddypro/LI-COR_GHG_File_Format.html
    https://github.com/JeremyRueffer/ClimateDataIO.jl#licor
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self.file = None
        # Files inside
        self.metadata = configparser.ConfigParser()
        self.data = DataFile(self)
        self.biomet_metadata = configparser.ConfigParser()
        self.biomet_data = DataFile(self)

    def __read_metadata(self, config, filepath):
        with self.file.open(filepath) as file:
            config.read_file(io.TextIOWrapper(file))

    def __enter__(self):
        self.file = ZipFile(self.filepath)
        filename = os.path.basename(self.filepath)
        root, ext = os.path.splitext(filename)
        # Read metadata files
        self.__read_metadata(self.metadata, root + '.metadata')
        self.__read_metadata(self.biomet_metadata, root + '-biomet.metadata')
        # Open data files
        self.data.open(root + '.data')
        self.biomet_data.open(root + '-biomet.data')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.data.close()
        self.biomet_data.close()
        self.file.close()


# For trying purposes
if __name__ == '__main__':
    filepath = sys.argv[1]
    with LicorParser(filepath) as parser:
        print(parser.biomet_metadata.sections())
        print(parser.biomet_data.header)
        print(parser.biomet_data.fields)
        for time, data in parser.biomet_data:
            print(time)
