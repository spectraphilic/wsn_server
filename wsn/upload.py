# Standard Library
import lzma
import os
import time
import traceback

# Django
from django.conf import settings
from django.core.management.base import BaseCommand

# App
from wsn.clickhouse import ClickHouse
from wsn.models import Metadata, Frame
from wsn.parsers.base import EmptyError, TruncatedError


ARCHIVE = os.path.join(settings.BASE_DIR, 'var', 'archive')


def upload2pg(name, metadata, fields, rows):
    """
    The metadata may be provided externally, as some files don't include
    metadata.
    """
    metadata, created = Metadata.get_or_create(metadata)
    for t, data in rows:
        Frame.create(metadata, t, None, data, update=False)

    return metadata


def upload2ch(name, metadata, fields, rows):
    if len(rows) > 0:
        with ClickHouse() as clickhouse:
            clickhouse.upload(name, metadata, fields, rows)


def archive(name, filename, data):
    # Create parent dirs
    dirpath = os.path.join(ARCHIVE, name)
    os.makedirs(dirpath, exist_ok=True)

    # Compress and save file
    filepath = os.path.join(dirpath, filename) + '.xz'
    with lzma.open(filepath, 'w') as f:
        f.write(data)


class ImportCommand(BaseCommand):

    # Variables to be overriden by subclasses
    EXTENSION = None
    PARSER = None

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+',
            help='Path to file or directory',
        )
        parser.add_argument('--skip', default=5,
            help='Skip files older than the given minutes (default 5)',
        )

    def archive(self, filename):
        data = open(filename, 'rb').read()
        with lzma.open(filename + '.xz', 'w') as f:
            f.write(data)
        os.remove(filename)

    def handle_file(self, filepath, stat):
        # If the file has been modified within the last few minutes, skip it.
        # This is a safety measure, just in case the file has not been
        # completely uploaded.
        if stat.st_mtime > self.upto:
            self.stdout.write(f"{filepath} skip for now, will handle later")
            return

        # Parse file
        try:
            metadata, fields, rows = self.PARSER(filepath).parse()
        except EmptyError:
            self.stderr.write(f'{filepath} WARNING file is empty')
            os.rename(filepath, f'{filepath}.empty')
            return
        except TruncatedError:
            self.stderr.write(f'{filepath} WARNING file is truncated')
            os.rename(filepath, f'{filepath}.truncated')
            return
        except Exception:
            self.stderr.write(f"{filepath} ERROR")
            traceback.print_exc(file=self.stderr)
            return

        self._handle_file(filepath, metadata, fields, rows)

    def handle(self, *args, **kw):
        self.upto = time.time() - (kw['skip'] * 60)

        for path in kw['paths']:
            # File
            if os.path.isfile(path):
                self.handle_file(path, os.stat(path))
                continue

            # Directory
            for entry in os.scandir(path):
                filepath = entry.path
                if not filepath.endswith(self.EXTENSION):
                    continue

                self.handle_file(filepath, entry.stat())

        return 0
