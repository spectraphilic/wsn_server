import fnmatch
import os
import pathlib
import time
import traceback
import zipfile

try:
    import tomllib as toml
except ImportError:
    # TODO Remove once we upgrde to Python 3.11
    import toml

# Django
from django.core.management.base import BaseCommand
from django.template.defaultfilters import filesizeformat

# Project
from wsn.parsers.base import EmptyError, TruncatedError
from wsn.parsers.cr6 import CR6Parser
from wsn.parsers.licor import LicorParser
from wsn.parsers.schemas import Schema
from wsn.parsers.sommer import SommerParser
from wsn.upload import upload2pg, upload2ch


PARSERS = {
    '.csv': SommerParser, # Sommer MRL-7
    '.dat': CR6Parser,
    '.ghg': LicorParser,
}


class Command(BaseCommand):
    """Django management command for importing data files into the database."""

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Import only the given name from the config file")
        parser.add_argument('--root', help="Root path to search for data files")
        parser.add_argument('--skip', default=5, type=int,
            help='Skip files older than the given minutes (default 5)',
        )

    def handle_file(self, filepath, stat, database, table_name, schema, strict):
        Parser = PARSERS.get(filepath.suffix)
        if Parser is None:
            return

        # If the file has been modified within the last few minutes, skip it.
        # This is a safety measure, just in case the file has not been
        # completely uploaded.
        if stat.st_mtime > self.upto:
            self.stdout.write(f"{filepath} skip for now, will handle later")
            return

        if type(schema) is str:
            schema = Schema(schema, strict)

        # Parse file
        try:
            parser = Parser(filepath, stat=stat, schema=schema)
            metadata, fields, rows = parser.parse()
        except EmptyError:
            self.stderr.write(f'{filepath} WARNING file is empty')
            os.rename(filepath, f'{filepath}.empty')
            return
        except TruncatedError:
            self.stderr.write(f'{filepath} WARNING file is truncated')
            os.rename(filepath, f'{filepath}.truncated')
            return
        except UnicodeDecodeError:
            # Sometimes Sommer files have garbage
            self.stderr.write(f'{filepath} WARNING file is not UTF-8')
            os.rename(filepath, f'{filepath}.badutf8')
            return
        except zipfile.BadZipFile:
            self.stderr.write(f'{filepath} WARNING bad zip file')
            os.rename(filepath, f'{filepath}.badzip')
            return
        except Exception:
            self.stderr.write(f"{filepath} ERROR")
            traceback.print_exc(file=self.stderr)
            return

        # Upload
        try:
            if database == 'postgres':
                # TODO Remove postgres: we only have 1 data source using this, move to ClickHouse
                upload2pg(table_name, metadata, fields, rows)
            else:
                upload2ch(table_name, metadata, fields, rows, schema)
        except Exception:
            self.stderr.write(f"{filepath} ERROR")
            traceback.print_exc(file=self.stderr)
            return

        # Archive file
        original_size = os.path.getsize(filepath)
        self.stdout.write(f"{filepath} file uploaded")
        dst = parser.archive()
        self.stdout.write(f"{filepath} file archived to {dst}")
        # Print statistics
        compressed_size = os.path.getsize(dst)
        ratio = compressed_size / original_size if original_size > 0 else 0
        ratio = ratio * 100
        self.stdout.write(
            f"Size from {filesizeformat(original_size)} to {filesizeformat(compressed_size)} "
            f"({ratio:.0f} % of the original)"
        )

    def handle(self, config, name, root, skip, *args, **kwargs):
        config = toml.load(config)
        config = config['import']
        root = pathlib.Path(root or config['root'])

        self.upto = time.time() - (skip * 60)

        for table_name, values in config.items():
            if not isinstance(values, dict):
                continue

            if name and table_name != name:
                continue

            # Proceed
            path = root / values['path']
            pattern = values['pattern']
            database = values.get('database', 'clickhouse')
            table_name = values.get('table', table_name)
            schema = values.get('schema', 'default')
            strict = values.get('schema-strict', False)

            for entry in os.scandir(path):
                if not entry.is_file():
                    continue

                path = pathlib.Path(entry.path)
                if fnmatch.fnmatch(path.name, pattern):
                    self.handle_file(path, entry.stat(), database, table_name, schema, strict)

        return 0
