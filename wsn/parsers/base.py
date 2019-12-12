# Standard Library
import logging
import os

# Project
from wsn.utils import cached_property


logger = logging.getLogger(__name__)



class EmptyError(Exception):
    pass

class TruncatedError(Exception):
    pass


class BaseParser:

    OPEN_KWARGS = {}

    def __init__(self,
        file,          # A file-like object or a path to a file
        filepath=None, # Used for better error messages
        metadata=None, # Externally provided metadata
        stat=None,     # os.stat_result instance
    ):

        if type(file) is str:
            assert filepath is None
            filepath = file
            self.file = open(filepath, **self.OPEN_KWARGS)
            self.managed = True
        else:
            self.file = file
            self.managed = False

        if filepath is not None:
            self.filepath = filepath

        if metadata is not None:
            assert type(metadata) is dict
            self.metadata = metadata

        if stat is not None:
            self.stat = stat

    @cached_property
    def filepath(self):
        return self.file.name

    @cached_property
    def stat(self):
        if self.filepath is not None:
            return os.stat(self.filepath)

        return None

    @cached_property
    def size(self):
        if self.stat is not None:
            return self.stat.st_size

        f = self.file
        f.seek(0, os.SEEK_END)
        self.size = f.tell()

    def parse(self):
        """
        Input may be a path to a file or an open file.
        """
        try:
            self._open()
            self._load()
            return (self.metadata, self.fields, self.rows)
        finally:
            self._close()
            if self.managed:
                self.file.close()

    def _open(self):
        pass

    def _load(self):
        raise NotImplementedError()

    def _close(self):
        pass


class CSVParser(BaseParser):

    OPEN_KWARGS = {'newline': ''}

    def _parse_value(self, name, unit, value):
        raise NotImplementedError()

    def _parse_row(self, row):
        data = {}
        for i, name in enumerate(self.fields):
            unit = self.units[i]
            value = row[i]
            try:
                value = self._parse_value(name, unit, value)
            except Exception:
                lineno = self.reader.line_num
                logger.exception(
                    f'error in file {self.filepath} at row {lineno} column {i}'
                )
                raise
            data[name] = value

        return data

    def _parse_time(self, data):
        raise NotImplementedError()

    def _parse_header(self):
        raise NotImplementedError()

    def _load(self):
        self._parse_header()

        rows = self.rows = []
        for row in self.reader:
            data = self._parse_row(row)
            time, data = self._parse_time(data)
            rows.append((time, data))
