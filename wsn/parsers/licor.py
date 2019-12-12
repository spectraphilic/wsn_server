# Standard Library
import configparser
import csv
import datetime
import io
import os
import sys
from zipfile import ZipFile

# Project
from wsn.utils import cached_property
from .base import BaseParser


class DataFile:

    def __init__(self, parser):
        self.file = None
        self.parser = parser
        self.reader = None
        self.header = {}
        self.fields = []

    def open(self, filename):
        self.file = io.TextIOWrapper(self.parser.zipfile.open(filename))
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


class LicorParser(BaseParser):
    """
    Licor.

    https://www.licor.com/env/help/eddypro/topics_eddypro/LI-COR_GHG_File_Format.html
    https://github.com/JeremyRueffer/ClimateDataIO.jl#licor
    """

    OPEN_KWARGS = {'mode': 'rb'}

    @cached_property
    def zipfile(self):
        return ZipFile(self.file)

    @cached_property
    def filename_root(self):
        filename = os.path.basename(self.filepath)
        root, ext = os.path.splitext(filename)
        return root

    @cached_property
    def _metadata(self):
        path = f'{self.filename_root}.metadata'
        config = configparser.ConfigParser()
        with self.zipfile.open(path) as file:
            config.read_file(io.TextIOWrapper(file))
        return config

    @cached_property
    def _data(self):
        data = DataFile(self)
        data.open(f'{self.filename_root}.data')
        return data

    @cached_property
    def _biomet_metadata(self):
        path = f'{self.filename_root}-biomet.metadata'
        config = configparser.ConfigParser()
        with self.zipfile.open(path) as file:
            config.read_file(io.TextIOWrapper(file))
        return config

    @cached_property
    def _biomet_data(self):
        data = DataFile(self)
        data.open(f'{self.filename_root}-biomet.data')
        return data

    def _load(self):
        self.metadata = self._data.header
        self.fields = self._data.fields
        self.rows = list(self._data)

    def _close(self):
        self._data.close()
        self._biomet_data.close()
        self.zipfile.close()


# For trying purposes
if __name__ == '__main__':
    filepath = sys.argv[1]
    parser = LicorParser(filepath)
    print(parser._biomet_metadata.sections())
    print(parser._biomet_data.header)
    print(parser._biomet_data.fields)
    for time, data in parser._biomet_data:
        print(time)
