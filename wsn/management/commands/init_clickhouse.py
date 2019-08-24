# Standard Library
import glob
import lzma
import os
import re
import traceback

# Requirements
from django.core.management.base import BaseCommand
import tqdm

# Project
from wsn.clickhouse import ClickHouse
from wsn.parsers.cr6 import CR6Parser


class Command(BaseCommand):

    parser = CR6Parser

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+',
                            help='Path to file or directory')

    def sort_files(self, paths):
        expr = re.compile('(.*)_(....-..-..)_(..-..-..)_(.*).dat.xz')
        def key(filepath):
            basename = os.path.basename(filepath)
            match = expr.match(basename)
            group = match.group
            # name, date, time, number
            return group(1), group(2), group(3), int(group(4))

        return sorted(paths, key=key)

    def handle_file(self, filepath):
        with lzma.open(filepath, 'rt', newline='') as f:
            with ClickHouse() as clickhouse:
                try:
                    return clickhouse.upload(self.parser, f, filepath)
                except Exception:
                    self.stderr.write(f"{filepath} ERROR")
                    traceback.print_exc()

    def handle_dir(self, path):
        filepaths = glob.glob(f'{path}/*.dat.xz')
        filepaths = self.sort_files(filepaths)

        for filepath in tqdm.tqdm(filepaths):
            metadata = self.handle_file(filepath)
            first = None
            if metadata is not None:
                metadata.pop('prog_signature')
                metadata.pop('prog_name')
                if first is None:
                    first = metadata
                else:
                    assert first == metadata

    def handle(self, *args, **kw):
        for path in kw['paths']:
            if os.path.isfile(path):
                self.handle_file(path)
            else:
                self.handle_dir(path)
