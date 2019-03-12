import logging


logger = logging.getLogger(__name__)


class BaseParser:

    def __init__(self, file):
        """
        Input may be a path to a file or an open file.
        """
        if type(file) is str:
            self.filepath = file
            self.file = None
        else:
            self.filepath = None
            self.file = file

    def __enter__(self):
        """
        To be used as a context manager, in particular if the input is the path
        to a file.
        """
        if self.filepath is not None:
            self.file = open(self.filepath)

        try:
            self.parse_header()
        except Exception:
            self.__exit__(None, None, None)
            raise

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.filepath is not None:
            self.file.close()

    def parse_header(self):
        raise NotImplementedError()

    @property
    def metadata(self):
        raise NotImplementedError()

    def __iter__(self):
        raise NotImplementedError()


class CSVParser(BaseParser):

    def parse_value(self, name, unit, value):
        raise NotImplementedError()

    def parse_row(self, row):
        data = {}
        for i, value in enumerate(row):
            name = self.fields[i]
            unit = self.units[i]
            try:
                value = self.parse_value(name, unit, value)
            except Exception:
                lineno = self.reader.line_num
                logger.exception(
                    f'error in file {self.filepath} at row {lineno} column {i}'
                )
                raise
            data[name] = value

        return data

    def parse_time(self, data):
        raise NotImplementedError()

    def __iter__(self):
        # FIXME Should reject a line if it doesn't have an end-of-line, because
        # then the last value is probably truncated.  Better to reject the
        # whole line than to import a bad value, right?
        # But the csv module has already stripped the end-of-line, so we cannot
        # know.
        for row in self.reader:
            data = self.parse_row(row)
            time, data = self.parse_time(data)
            yield time, data
