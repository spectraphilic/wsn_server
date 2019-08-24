# Standard Library
import lzma
import os
import time
import traceback

# Django
from django.core.management.base import BaseCommand

# Project
#from wsn.clickhouse import ClickHouse
from wsn.parsers.cr6 import CR6Parser
from wsn.upload import upload


def archive(filename):
    data = open(filename, 'rb').read()
    with lzma.open(filename + '.xz', 'w') as f:
        f.write(data)
    os.remove(filename)


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

        if stat.st_size == 0:
            self.stderr.write(f'{filepath} WARNING file is empty')
            os.rename(filepath, f'{filepath}.empty')
            return

        # TODO Remove once we move to ClickHouse definitely
        try:
            upload(self.parser, filepath)
        except Exception:
            self.stderr.write(f"{filepath} ERROR")
            traceback.print_exc()
            return

#       with ClickHouse as clickhouse:
#           try:
#               clickhouse.upload(self.parser, filepath)
#           except Exception:
#               self.stderr.write(f"{filepath} ERROR")
#               traceback.print_exc()
#               return

        # Archive file
        self.stdout.write(f"{filepath} file uploaded")
        archive(filepath)
        self.stdout.write(f"{filepath} file archived")

    def handle(self, *args, **kw):
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
