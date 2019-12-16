# Standard Library
import lzma
import os
import pathlib
import time
import traceback

# Django
from django.core.management.base import BaseCommand

# Project
from wsn.parsers.base import EmptyError, TruncatedError
from wsn.parsers.cr6 import CR6Parser
from wsn.parsers.licor import LicorParser
from wsn.parsers.sommer import SommerParser
from wsn.upload import upload2pg, upload2ch


CONFIG = {
    'eton2': [upload2pg],
    'finseflux': [upload2ch],
    'mobileflux': [upload2ch],
    'sommer': [upload2ch],
}

PARSERS = {
    '.csv': SommerParser, # Sommer MRL-7
    '.dat': CR6Parser,
    '.ghg': LicorParser,
}


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+',
            help='Path to file or directory',
        )
        parser.add_argument('--name',
            help="Database table name, by default it's inferred from the filepath and file contents",
        )
        parser.add_argument('--skip', default=5,
            help='Skip files older than the given minutes (default 5)',
        )

    def archive(self, filename):
        data = open(filename, 'rb').read()
        with lzma.open(f'{filename}.xz', 'w') as f:
            f.write(data)
        os.remove(filename)

    def handle_file(self, filepath, stat):
        parser = PARSERS.get(filepath.suffix)
        if parser is None:
            return

        # If the file has been modified within the last few minutes, skip it.
        # This is a safety measure, just in case the file has not been
        # completely uploaded.
        if stat.st_mtime > self.upto:
            self.stdout.write(f"{filepath} skip for now, will handle later")
            return

        # Parse file
        try:
            metadata, fields, rows = parser(filepath, stat=stat).parse()
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

        dirpath, filename = os.path.split(filepath)
        dirname = os.path.basename(dirpath)

        # Upload
        for upload_to in CONFIG[dirname]:
            try:
                upload_to(self.name or dirname, metadata, fields, rows)
            except Exception:
                self.stderr.write(f"{filepath} ERROR")
                traceback.print_exc(file=self.stderr)
                return

        # Archive file
        self.stdout.write(f"{filepath} file uploaded")
        self.archive(filepath)
        self.stdout.write(f"{filepath} file archived")

    def handle(self, *args, **kw):
        self.name = kw.get('name')
        self.upto = time.time() - (kw['skip'] * 60)

        for path in kw['paths']:
            path = pathlib.Path(path)

            # File
            if path.is_file():
                self.handle_file(path, path.stat())
                continue

            # Directory
            for entry in os.scandir(path):
                path = pathlib.Path(entry.path)
                self.handle_file(path, entry.stat())

        return 0
