# Standard Library
import glob
import lzma
import os
import traceback

# Requirements
from django.core.management.base import BaseCommand
import tqdm

# Project
from wsn.parsers.base import EmptyError, TruncatedError
from wsn.parsers.cr6 import CR6Parser
from wsn.upload import upload2ch


class Command(BaseCommand):

    parser = CR6Parser

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+',
                            help='Path to file or directory')

    def sort_files(self, paths):
        n = len('.dat.xz')
        def key(filepath):
            name = os.path.basename(filepath)
            assert name.endswith('.dat.xz')
            name = name[:-n]

            key = []
            for segment in name.split('_'):
                try:
                    key.append(int(segment))
                except ValueError:
                    key.append(segment)

            return tuple(key)

        return sorted(paths, key=key)

    def handle_file(self, filepath):
        with lzma.open(filepath, 'rt', newline='') as f:
            try:
                metadata, fields, rows = self.parser().parse(f, filepath)
            except (EmptyError, TruncatedError):
                return None, [], []
            except Exception:
                self.stderr.write(f"{filepath} ERROR")
                traceback.print_exc(file=self.stderr)
                return None, [], []

        return metadata, fields, rows


    def handle_dir(self, path):
        dirname = os.path.basename(path)

        filepaths = glob.glob(f'{path}/*.dat.xz')
        filepaths = self.sort_files(filepaths)

        # Batch inserts
        add_fields = set()
        add_rows = []

        first = None
        for filepath in tqdm.tqdm(filepaths):
            metadata, new_fields, new_rows = self.handle_file(filepath)
            if metadata is None:
                continue

            metadata.pop('prog_signature')
            metadata.pop('prog_name')
            if first is None:
                first = metadata

            if metadata != first:
                upload2ch(dirname, first, add_fields, add_rows)
                first = None
                add_fields = set()
                add_rows = []

            new_fields = set(new_fields)
            if add_fields ^ new_fields:
                upload2ch(dirname, metadata, add_fields, add_rows)
                add_fields = set()
                add_rows = []

            # Append new rows
            add_fields = new_fields
            add_rows.extend(new_rows)
            if len(add_rows) >= 10000:
                upload2ch(dirname, metadata, add_fields, add_rows)
                add_fields = set()
                add_rows = []
        else:
            upload2ch(dirname, metadata, add_fields, add_rows)


    def handle(self, *args, **kw):
        for path in kw['paths']:
            if os.path.isfile(path):
                dirpath, filename = os.path.split(path)
                dirname = os.path.basename(dirpath)
                metadata, fields, rows = self.handle_file(path)
                upload2ch(dirname, metadata, fields, rows)
            else:
                self.handle_dir(path)
