import datetime
import logging
import lzma
import os
import re
import shutil
import tarfile
import zipfile
from pathlib import Path

# Django
from django.utils.functional import cached_property

# Project
from wsn.parsers.schemas import Schema

logger = logging.getLogger(__name__)


class EmptyError(Exception):
    pass

class TruncatedError(Exception):
    pass


DATE_RE = re.compile(r'(?<![\d-])(\d{4})[-_](\d{2})[-_](\d{2})(?!\d)')


def parse_filename_date(name):
    """
    Extract the date from a data filename, e.g.
    'HFData_2026-07-01_01-00-00_639.dat' -> datetime.date(2026, 7, 1).
    Raises ValueError if the filename contains no valid date.
    """
    match = DATE_RE.search(name)
    if match is None:
        raise ValueError(f'no date found in filename: {name}')
    return datetime.date(int(match[1]), int(match[2]), int(match[3]))


# The earliest timestamp accepted on import: the project started in 2015,
# nothing before that is real data (e.g. loggers with a dead battery clock
# reset to 1970 or 1999).
MIN_TIMESTAMP = datetime.datetime(2015, 1, 1, tzinfo=datetime.UTC)

# Rows are rejected if their timestamp is more than this many days after
# the date in the filename. A file accumulates rows from its creation (the
# filename date) until the logger rotates the file; the longest rotation in
# the fleet is weekly (eton2), so this is ~8x headroom, and it also covers
# rotation schedules deployed in the future. The bound is relative to the
# filename date, not to today, so importing the same archive always yields
# the same result.
FUTURE_WINDOW_DAYS = 60


def check_row_time(time, filename_date):
    """
    Return a reason string if the row's timestamp cannot be right, else
    None: before the start of the project, or implausibly after the date in
    the filename (logger clock issues).
    """
    if time is None:
        return 'no timestamp'

    if isinstance(time, (int, float)):  # epoch
        time = datetime.datetime.fromtimestamp(time, tz=datetime.UTC)

    if not isinstance(time, datetime.datetime):
        return f'unexpected timestamp type: {type(time).__name__}'

    if time.tzinfo is None:
        return 'naive timestamp, expected UTC'

    if time < MIN_TIMESTAMP:
        return f'timestamp {time} is before {MIN_TIMESTAMP.date()}'

    if time.date() > filename_date + datetime.timedelta(days=FUTURE_WINDOW_DAYS):
        return (f'timestamp {time.date()} is more than {FUTURE_WINDOW_DAYS} '
                f'days after the filename date {filename_date}')

    return None


def validate_rows(rows, filename):
    """
    Split (time, data) rows into good rows and bad rows based on the date in
    the filename: a row is bad if its timestamp is before the start of the
    project or more than FUTURE_WINDOW_DAYS after it. Bad rows carry a human
    readable reason; they are dropped for now, later they may go to a
    quarantine table.

    Raises ValueError if the filename contains no date.
    """
    filename_date = parse_filename_date(filename)
    good, bad = [], []
    for time, data in rows:
        reason = check_row_time(time, filename_date)
        if reason is None:
            good.append((time, data))
        else:
            bad.append((time, data, reason))

    return good, bad


def get_archive_root(filepath, import_dir):
    """
    Return the root directory under which the archive/ directory lives:
    the parent of 'raw' if present, else the import directory itself.
    """
    parts = list(filepath.parts)
    if 'raw' in parts:
        return Path(*parts[:parts.index('raw')])
    return import_dir


def get_archive_dir_path(filepath, import_dir=None):
    """
    Return the directory a file is archived to: <root>/archive/<YYYY>/<MM>/,
    where the date comes from the filename (strict: raises ValueError if the
    filename contains no valid date).
    """
    if import_dir is None:
        import_dir = filepath.parent
    root = get_archive_root(filepath, import_dir)
    date = parse_filename_date(filepath.name)
    return root / 'archive' / str(date.year) / f'{date.month:02d}'


def unarchive(src, dirpath):
    """
    Extract an archived file into dirpath (which must exist), restoring its
    original form: 'name.dat.xz' -> 'name.dat', 'name.tar.xz' -> 'name.ghg'
    (the zip is rebuilt from the tar members, see LicorParser.archive()).
    Returns the path of the extracted file.
    """
    src = Path(src)
    name = src.name.removesuffix('.xz')
    if name.endswith('.tar'):
        # Only Licor archives as tar.xz; the archived name is <name>.tar.xz,
        # the original .ghg suffix is not preserved, restore it
        dst = Path(dirpath) / (name.removesuffix('.tar') + '.ghg')
        with tarfile.open(src, 'r:xz') as tar, zipfile.ZipFile(dst, 'w') as zf:
            for member in tar.getmembers():
                if member.isfile():
                    zf.writestr(member.name, tar.extractfile(member).read())
        return dst

    dst = Path(dirpath) / name
    with lzma.open(src) as fsrc, open(dst, 'wb') as fdst:
        shutil.copyfileobj(fsrc, fdst)
    return dst


class BaseParser:

    OPEN_KWARGS = {}

    def __init__(self,
        file,          # A file-like object or a path to a file
        filepath=None, # Used for better error messages
        metadata=None, # Externally provided metadata
        stat=None,     # os.stat_result instance
        schema=None,   # used to desirialize values
    ):

        if type(file) is str:
            file = Path(file)

        if isinstance(file, Path):
            assert filepath is None
            filepath = file
            self.file = open(filepath, **self.OPEN_KWARGS)
            self.managed = True
        else:
            self.file = file
            self.managed = False

        if filepath is not None:
            self.filepath = filepath
            self.check_filepath(filepath)

        metadata = metadata or {}
        assert type(metadata) is dict
        self.metadata = metadata

        if stat is not None:
            self.stat = stat

        if schema is None:
            schema = Schema('default')

        self.schema = schema

    @cached_property
    def filepath(self):
        return Path(self.file.name)

    @cached_property
    def stat(self):
        if self.filepath is not None:
            return self.filepath.stat()

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

    def check_filepath(self, filepath):
        pass

    @staticmethod
    def get_archive_date(name):
        """
        Date used for the archive/<YYYY>/<MM>/ directory. By default it comes
        from the filename (strict); parsers may override it.
        """
        return parse_filename_date(name)

    @classmethod
    def get_archive_relpath(cls, filepath):
        """
        Return the path of the archived file relative to the entry's
        archive/ directory, e.g. Path('2026/10/name.dat.xz'). Raises
        ValueError if no date can be extracted from the filename.
        """
        filepath = Path(filepath)
        date = cls.get_archive_date(filepath.name)
        return Path(str(date.year)) / f'{date.month:02d}' / f'{filepath.name}.xz'

    def archive(self):
        src = self.filepath
        relpath = self.get_archive_relpath(src)
        dirpath = get_archive_root(src, src.parent) / 'archive' / relpath.parent
        dirpath.mkdir(parents=True, exist_ok=True)
        dst = dirpath / relpath.name
        with open(src, 'rb') as fsrc, lzma.open(dst, 'w') as fdst:
            shutil.copyfileobj(fsrc, fdst)
        os.remove(src)
        return dst


class CSVParser(BaseParser):

    OPEN_KWARGS = {'newline': ''}

    def _parse_value(self, name, unit, value):
        raise NotImplementedError()

    def _parse_row(self, row):
        data = {}
        for i, name in enumerate(self.fields):
            unit = self.units[i]
            try:
                value = row[i]
            except IndexError:
                value = ''
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
            if data is not None:
                time, data = self._parse_time(data)
                rows.append((time, data))
