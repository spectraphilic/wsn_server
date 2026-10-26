import datetime
import fcntl
import fnmatch
import os
import pathlib
import time
import tomllib
import traceback
import zipfile

# Django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import filesizeformat

# Project
from wsn.models import ImportFile
from wsn.parsers import PARSERS
from wsn.parsers.base import EmptyError, TruncatedError
from wsn.parsers.schemas import Schema


# A file's date comes from the logger's clock at file creation, so it
# cannot be in the future: a file dated further ahead means the clock is
# wrong and both the filename and the rows inside are untrustworthy. Such
# files are renamed aside for a human to inspect, like truncated files;
# the rename also takes them out of the entry's pattern.
FUTURE_FILE_DAYS = 2


class Command(BaseCommand):
    """
    Archive data files and register them in the wsn_importfile table.

    Entries with pipeline = "archive_first" are archived and registered; the
    data itself is imported later by the file_import command, which marks the
    rows as done. Entries with pipeline = "archive_only" are archived without
    registering them, their data is never imported.
    """

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Archive only the given name from the config file")
        parser.add_argument('--skip', default=10, type=int,
            help='Skip files modified within the last given minutes (default 10)',
        )

    def handle_file(self, filepath, stat, name, schema, strict, archive_only=False):
        Parser = PARSERS.get(filepath.suffix)
        if Parser is None:
            return

        # If the file has been modified within the last few minutes, skip it.
        # This is a safety measure, just in case the file has not been
        # completely uploaded.
        if stat.st_mtime > self.upto:
            self.stdout.write(f"{filepath} skip for now, will handle later")
            return

        # The date in the filename comes from the logger's clock at file
        # creation, it cannot be in the future: a future-dated file means
        # the clock is wrong. Rename it aside for a human to inspect.
        try:
            file_date = Parser.get_archive_date(filepath.name)
        except ValueError:
            file_date = None
        limit = datetime.date.today() + datetime.timedelta(days=FUTURE_FILE_DAYS)
        if file_date is not None and file_date > limit:
            self.stderr.write(
                f"{filepath} WARNING filename date {file_date} is more than "
                f"{FUTURE_FILE_DAYS} days in the future, renamed"
            )
            os.rename(filepath, f'{filepath}.future')
            return

        # The archive path is fully determined by the filename, so we can
        # check whether the file was already archived before parsing it.
        # This happens when a file with the same name is re-uploaded within
        # the same month. Archive-only entries have no rows, so a re-uploaded
        # file is archived again, as in the old pipeline.
        if not archive_only:
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
        if archive_only:
            self.stdout.write(f"{filepath} archived only, not registered")
        else:
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

                # The new pipeline handles "archive_first" and "archive_only"
                # entries, the old pipeline is selected explicitly with
                # "import_first" (also the default when the key is absent),
                # and an empty value disables the entry
                pipeline = values.get('pipeline', 'import_first')
                if pipeline not in ('archive_first', 'archive_only'):
                    if pipeline not in ('import_first', ''):
                        self.stderr.write(
                            f"{entry_name}: WARNING unknown pipeline value {pipeline!r}")
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
                        self.handle_file(filepath, entry.stat(), entry_name,
                                         schema, strict,
                                         archive_only=(pipeline == 'archive_only'))

        return 0
