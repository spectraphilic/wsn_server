# Standard Library
import lzma
import os
import time
import traceback

# Django
from django.core.management.base import BaseCommand

from wsn.upload import CR6Uploader


def archive(filename):
    data = open(filename, 'rb').read()
    with lzma.open(filename + '.xz', 'w') as f:
        f.write(data)
    os.remove(filename)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+',
                            help='Path to file or directory')

    def handle_file(self, filepath, stat):
        # If the file has been modified within the last 15min, skip it.  This
        # is a safety measure, just in case the file has not been completely
        # uploaded.
        if stat.st_mtime > self.upto:
            self.stdout.write("{} skip for now, will handle later".format(filepath))
            return

        if stat.st_size == 0:
            self.stdout.write("{} WARNING file is empty".format(filepath))
            return

        try:
            self.uploader.upload(filepath)
        except Exception:
            self.stderr.write("{} ERROR".format(filepath))
            traceback.print_exc()
        else:
            self.stdout.write("{} file uploaded".format(filepath))
            archive(filepath)
            self.stdout.write("{} file archived".format(filepath))

    def handle(self, *args, **kw):
        self.uploader = CR6Uploader()
        self.upto = time.time() - 60 * 15 # 15 minutes ago

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
