import configparser
import csv
import datetime
import io
import lzma
import os
import pathlib
import sys
import tarfile
import time
import zipfile

# Django
from django.utils.functional import cached_property

# Project
from .base import BaseParser
from .utils import clean_column_name


def zip_to_tar_xz(zip_path, tar_xz_path):
    with (
        zipfile.ZipFile(zip_path, 'r') as zip_ref,
        lzma.open(tar_xz_path, 'wb') as xz_file,
        tarfile.open(fileobj=xz_file, mode='w|') as tar_ref
    ):

        for file_info in zip_ref.infolist():
            # Create TarInfo object
            tar_info = tarfile.TarInfo(name=file_info.filename)
            tar_info.size = file_info.file_size

            # Convert ZIP's date_time tuple to Unix timestamp
            # Assume it's UTC (TODO Parse the UT extra field)
            if hasattr(file_info, 'date_time'):
                dt_tuple = file_info.date_time
                dt_utc = datetime.datetime(*dt_tuple, tzinfo=datetime.timezone.utc)
                tar_info.mtime = int(dt_utc.timestamp())

            # Add file to tar
            with zip_ref.open(file_info) as file_obj:
                tar_ref.addfile(tar_info, fileobj=file_obj)


def get_archive_dir_path(path):
    """
    Convert a raw file path to an archive directory path.

    Example:
        Input:  "data/licor/myr2/raw/[...]/2025-06-09T143000_AIU-2084.ghg"
        Output: "data/licor/myr2/archive/2025/"
    """
    # Get the root directory, the common ancestor of raw and archive
    parts = list(path.parts)
    raw_index = parts.index('raw')
    root = pathlib.Path(*parts[:raw_index])

    # Extract date from filename (assuming it starts with YYYY-MM-DD)
    date = path.name[:len("2025-06-09")]
    date = datetime.datetime.strptime(date, "%Y-%m-%d")

    # Return the final path, create it if necessary
    path = root / 'archive' / str(date.year) / f'{date.month:02d}'
    return path


class DataFile:

    def __init__(self, parser):
        self.file = None
        self.parser = parser
        self.reader = None
        self.header = {}
        self.raw_fields = []
        self.fields = []
        self.cleaned_field_map = {}  # maps raw name → cleaned name

    def open(self, filename):
        self.file = io.TextIOWrapper(self.parser.zipfile.open(filename))
        self.parse()

    def close(self):
        self.file.close()

    def parse(self):
        schema = self.parser.schema

        self.reader = csv.reader(self.file, dialect='excel-tab')
        # Read Header
        for row in self.reader:
            if len(row) != 2:
                self.raw_fields = row
                assert 'TIMESTAMP' not in row

                # Build cleaned field names, skipping unneeded ones
                cleaned_fields = []
                self.cleaned_field_map = {}
                seen_cleaned = {}  # maps cleaned_name → first raw_name that produced it

                for raw_name in self.raw_fields:
                    field = schema.get_field(raw_name)
                    if field is None:
                        continue

                    if field.name == raw_name:
                        cleaned = clean_column_name(raw_name)
                    else:
                        cleaned = field.name

                    if cleaned in seen_cleaned:
                        # Conflict! Two different raw names map to same cleaned name
                        first_raw = seen_cleaned[cleaned]
                        raise ValueError(
                            f"Column name collision after cleaning: "
                            f"'{first_raw}' and '{raw_name}' both normalize to '{cleaned}'."
                        )

                    seen_cleaned[cleaned] = raw_name
                    self.cleaned_field_map[raw_name] = cleaned
                    cleaned_fields.append(cleaned)

                self.fields = ['TIMESTAMP'] + cleaned_fields
                break
            self.header[row[0]] = row[1]

    def __convert(self, value):
        try:
            return int(value)
        except ValueError:
            pass

        try:
            return float(value)
        except ValueError:
            return value

    def __iter__(self):
        schema = self.parser.schema

        if 'DATE' in self.raw_fields:
            i_date = self.raw_fields.index('DATE')
            i_time = self.raw_fields.index('TIME')
        else:
            i_date = self.raw_fields.index('Date')
            i_time = self.raw_fields.index('Time')

        def get_time(row):
            date = row[i_date]
            time, ms = row[i_time].rsplit(':', 1)
            dt = datetime.datetime.strptime(date + time, '%Y-%m-%d%H:%M:%S')
            dt = dt.replace(microsecond=int(ms) * 1000)
            dt = dt.replace(tzinfo=datetime.timezone.utc)
            # TODO Assert it matches Seconds/Nanoseconds
            return dt

        for row in self.reader:
            time = get_time(row)
            data = {}
            for i, value in enumerate(row):
                raw_name = self.raw_fields[i]
                if raw_name == 'DATAH':
                    assert value == 'DATA'

                field = schema.get_field(raw_name)
                if field is None:
                    continue

                cleaned_name = self.cleaned_field_map[raw_name]
                data[cleaned_name] = self.__convert(value)

            yield (time, data)


class LicorParser(BaseParser):
    """
    Licor.

    https://www.licor.com/support/EddyPro/topics/ghg-file-format.html
    https://github.com/JeremyRueffer/ClimateDataIO.jl#licor
    """

    OPEN_KWARGS = {'mode': 'rb'}

    @cached_property
    def zipfile(self):
        return zipfile.ZipFile(self.file)

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
        # Example of metadata
        # {
        #     'Model:': 'LI-7200 Enclosed CO2/H2O Analyzer',
        #     'SN:': '72H-0848',
        #     'Instrument:': 'LATICE-Flux_Finse',
        #     'File Type:': '2',
        #     'Software Version:': '8.7.5',
        #     'Timestamp:': '16:00:00',
        #     'Timezone:': 'UTC'
        # }
        self.metadata = self._data.header
        assert self.metadata['Timezone:'] == 'UTC'

        self.fields = self._data.fields
        self.rows = list(self._data)

    def _close(self):
        self._data.close()
        self._biomet_data.close()
        self.zipfile.close()

    def check_filepath(self, filepath):
        assert filepath.suffix == '.ghg'
        get_archive_dir_path(filepath)

    def archive(self):
        src = self.filepath
        dirpath = get_archive_dir_path(src)
        dirpath.mkdir(parents=True, exist_ok=True)
        dst = dirpath / src.with_suffix(".tar.xz").name
        zip_to_tar_xz(src, dst)
        os.remove(src)
        return dst


# For trying purposes
if __name__ == '__main__':
    filepath = sys.argv[1]
    parser = LicorParser(filepath)
    print(parser._biomet_metadata.sections())
    print(parser._biomet_data.header)
    print(parser._biomet_data.fields)
    for time, data in parser._biomet_data:
        print(time)
