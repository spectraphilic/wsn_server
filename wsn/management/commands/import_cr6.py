# Standard Library
import lzma
import os
import time
import traceback

# Django
from django.core.management.base import BaseCommand

# Project
from wsn.parsers.base import EmptyError, TruncatedError
from wsn.parsers.cr6 import CR6Parser
from wsn.upload import upload2pg, upload2ch


def archive(filename):
    data = open(filename, 'rb').read()
    with lzma.open(filename + '.xz', 'w') as f:
        f.write(data)
    os.remove(filename)


CONFIG = {
    'eton2': [upload2pg],
    'finseflux': [upload2ch],
    'mobileflux': [upload2ch],
}


class Command(BaseCommand):

    parser = CR6Parser

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+',
                            help='Path to file or directory')

    def handle_file(self, filepath, stat):
        # If the file has been modified within the last 15min, skip it.  This
        # is a safety measure, just in case the file has not been completely
        # uploaded.
        if stat.st_mtime > self.upto:
            self.stdout.write(f"{filepath} skip for now, will handle later")
            return

        # Parse file
        try:
            metadata, fields, rows = self.parser().parse(filepath)
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
            traceback.print_exc()
            return

        dirpath, filename = os.path.split(filepath)
        dirname = os.path.basename(dirpath)

        # Upload
        for upload_to in CONFIG.get(dirname, [upload2pg]):
            try:
                upload_to(dirname, metadata, fields, rows)
            except Exception:
                self.stderr.write(f"{filepath} ERROR")
                traceback.print_exc()
                return

        # Archive file
        self.stdout.write(f"{filepath} file uploaded")
        archive(filepath)
        self.stdout.write(f"{filepath} file archived")

    def handle(self, *args, **kw):
        self.upto = time.time() - 60 * 5 # 5 minutes ago

        for path in kw['paths']:
            # File
            if os.path.isfile(path):
                self.handle_file(path, os.stat(path))
                continue

            # Directory
            for entry in os.scandir(path):
                filepath = entry.path
                if not filepath.endswith('.dat'):
                    continue

                self.handle_file(filepath, entry.stat())
