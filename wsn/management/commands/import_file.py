import fnmatch
import os
import pathlib
import time
import traceback

import toml  # TODO Replace by tomllib after upgrading to Python 3.11

# Django
from django.core.management.base import BaseCommand
from django.template.defaultfilters import filesizeformat

# Project
from wsn.parsers.base import EmptyError, TruncatedError
from wsn.parsers.cr6 import CR6Parser
from wsn.parsers.licor import LicorParser
from wsn.parsers.sommer import SommerParser
from wsn.upload import upload2pg, upload2ch


# TODO Remove upload2pg: we only have 1 data source using this, move to ClickHouse
UPLOAD_TO = {
    "postgres": upload2pg,
    "clickhouse": upload2ch,
}

SCHEMA = {
    'mammamia3': {
        'TIMESTAMP': 'UInt32',
        'RECORD': 'UInt32',
        # Borehole
        'SurfaceTimeStamp': "DateTime('UTC')",
        # Surface
        'BoreholeTimeStamp': "DateTime64(3, 'UTC')",
        'FtpFileName_mm3_Borehole': 'String',
        'FtpFileName_mm3_Surface': 'String',
        'SfTimeStamp': "DateTime('UTC')",
        'TransmitTimeStamp': "DateTime64(3, 'UTC')",
    },
    'gruvebadet': {
        'TIMESTAMP': 'UInt32',
        'RECORD': 'UInt32',
        # Diagnostics
        'CompileResults': 'String',
        'OSVersion': 'String',
        'ProgName': 'String',
        'StartTime': "DateTime64(3, 'UTC')",
    },
    'finseflux_HFData': {
        'TIMESTAMP': "DateTime64(3, 'UTC')",
        'RECORD': 'UInt32',
    },
}

DEFAULT_LICOR_SCHEMA = {
    'TIMESTAMP': "DateTime64(3, 'UTC')",
}

DEFAULT_SCHEMA = {
    'TIMESTAMP': 'UInt32',
    'RECORD': 'UInt32',
}


PARSERS = {
    '.csv': SommerParser, # Sommer MRL-7
    '.dat': CR6Parser,
    '.ghg': LicorParser,
}


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Import only the given name from the config file")
        parser.add_argument('--root', help="Root path to search for data files")
        parser.add_argument('--skip', default=5, type=int,
            help='Skip files older than the given minutes (default 5)',
        )

    def handle_file(self, filepath, stat, upload_to, table_name):
        Parser = PARSERS.get(filepath.suffix)
        if Parser is None:
            return

        # If the file has been modified within the last few minutes, skip it.
        # This is a safety measure, just in case the file has not been
        # completely uploaded.
        if stat.st_mtime > self.upto:
            self.stdout.write(f"{filepath} skip for now, will handle later")
            return

        # Schema
        if upload_to is upload2ch:
            schema = SCHEMA.get(table_name)
            if table_name.startswith('licor_'):
                schema = DEFAULT_LICOR_SCHEMA
            elif schema is None:
                dirpath, filename = os.path.split(filepath)
                dirname = os.path.basename(dirpath)
                schema = SCHEMA.get(dirname, DEFAULT_SCHEMA)
        else:
            schema = None

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
        except Exception:
            self.stderr.write(f"{filepath} ERROR")
            traceback.print_exc(file=self.stderr)
            return

        # Upload
        try:
            upload_to(table_name, metadata, fields, rows, schema=schema)
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
            upload_to = UPLOAD_TO[database]
            for entry in os.scandir(path):
                if not entry.is_file():
                    continue

                path = pathlib.Path(entry.path)
                if fnmatch.fnmatch(path.name, pattern):
                    self.handle_file(path, entry.stat(), upload_to, table_name)

        return 0
