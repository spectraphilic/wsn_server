import fcntl
import fnmatch
import os
import pathlib
import time
import traceback
import zipfile

import tomllib

# Django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import filesizeformat

# Project
from wsn.models import ImportFile
from wsn.parsers import PARSERS
from wsn.parsers.base import EmptyError, TruncatedError
from wsn.parsers.schemas import Schema


class Command(BaseCommand):
    """
    Archive data files and register them in the wsn_importfile table.

    The data itself is not imported here; that is done later by the
    file_import command, which marks the rows as done.
    """

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Archive only the given name from the config file")
        parser.add_argument('--skip', default=10, type=int,
            help='Skip files modified within the last given minutes (default 10)',
        )

    def handle_file(self, filepath, stat, name, schema, strict):
        Parser = PARSERS.get(filepath.suffix)
        if Parser is None:
            return

        # If the file has been modified within the last few minutes, skip it.
        # This is a safety measure, just in case the file has not been
        # completely uploaded.
        if stat.st_mtime > self.upto:
            self.stdout.write(f"{filepath} skip for now, will handle later")
            return

        # The archive path is fully determined by the filename, so we can
        # check whether the file was already archived before parsing it.
        # This happens when a file with the same name is re-uploaded within
        # the same month.
        try:
            relpath = Parser.get_archive_relpath(filepath)
        except ValueError:
            self.stderr.write(f"{filepath} WARNING cannot archive, no date in filename")
            return

        path = str(relpath)
        if ImportFile.objects.filter(name=name, path=path).exists():
            self.stdout.write(f"{filepath} already archived, skipped")
            return

        if type(schema) is str:
            schema = Schema(schema, strict)

        # Parse file
        try:
            parser = Parser(filepath, stat=stat, schema=schema)
            metadata, fields, rows = parser.parse()
        except EmptyError:
            self.stdout.write(f'{filepath} WARNING file is empty, removed')
            os.remove(filepath)
            return
        except TruncatedError:
            self.stdout.write(f'{filepath} WARNING file is truncated')
            os.rename(filepath, f'{filepath}.truncated')
            return
        except UnicodeDecodeError:
            # Sometimes Sommer files have garbage
            self.stdout.write(f'{filepath} WARNING file is not UTF-8')
            os.rename(filepath, f'{filepath}.badutf8')
            return
        except zipfile.BadZipFile:
            self.stdout.write(f'{filepath} WARNING bad zip file')
            os.rename(filepath, f'{filepath}.badzip')
            return
        # Catch-all: a single bad file must not abort the whole run; it is
        # logged and left in place to be retried on the next run
        except Exception:  # noqa: BLE001
            self.stderr.write(f"{filepath} ERROR")
            traceback.print_exc(file=self.stderr)
            return

        # Archive file
        original_size = os.path.getsize(filepath)
        self.stdout.write(f"{filepath} file parsed")
        try:
            dst = parser.archive()
        except Exception:  # noqa: BLE001
            self.stderr.write(f"{filepath} ERROR archiving, file left in place")
            traceback.print_exc(file=self.stderr)
            return
        self.stdout.write(f"{filepath} file archived to {dst}")

        # Register the file; it will be imported by the file_import command
        _, created = ImportFile.objects.get_or_create(name=name, path=path)
        if not created:
            self.stderr.write(f"{filepath} WARNING already registered by another run")

        # Print statistics
        compressed_size = os.path.getsize(dst)
        ratio = compressed_size / original_size if original_size > 0 else 0
        ratio = ratio * 100
        self.stdout.write(
            f"Size from {filesizeformat(original_size)} to {filesizeformat(compressed_size)} "
            f"({ratio:.0f} % of the original)"
        )

    def handle(self, config, name, skip, *args, **kwargs):
        # Prevent overlapping runs (e.g. a slow cron run overlapping with
        # the next one). The lock is held until this command finishes, so
        # there are no stale locks. A second run fails loudly instead of
        # silently skipping.
        lockpath = settings.BASE_DIR / 'var' / 'run' / 'file_archive.lock'
        lockpath.parent.mkdir(parents=True, exist_ok=True)
        with open(lockpath, 'w') as lockfile:
            try:
                fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise CommandError('another file_archive run is in progress')

            with open(config, 'rb') as f:
                config = tomllib.load(f)
            config = config['import']

            self.upto = time.time() - (skip * 60)

            for entry_name, values in config.items():
                if not isinstance(values, dict):
                    continue

                # Only entries of the new pipeline
                if values.get('pipeline') != 'archive':
                    continue

                if name and entry_name != name:
                    continue

                # Proceed
                directory = pathlib.Path(values['path'])
                if not directory.is_absolute():
                    raise CommandError(f'{entry_name}: path must be absolute: {directory}')
                pattern = values['pattern']
                schema = values.get('schema', 'default')
                strict = values.get('schema-strict', False)

                for entry in os.scandir(directory):
                    if not entry.is_file():
                        continue

                    filepath = pathlib.Path(entry.path)
                    if fnmatch.fnmatch(filepath.name, pattern):
                        self.handle_file(filepath, entry.stat(), entry_name, schema, strict)

        return 0
