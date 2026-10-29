import fcntl
import fnmatch
import pathlib

import tomllib

# Django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Project
from wsn.models import ImportFile
from wsn.parsers import get_parser, get_raw_name
from wsn.parsers.base import get_archive_root


class Command(BaseCommand):
    """
    Register archived files in the wsn_importfile table.

    For every file found under an entry's archive/ directory a row is
    created, unless it exists already; the data itself is not imported here,
    that is done by the file_import command. This is also how a logger being
    migrated from the old pipeline is backfilled: files archived by
    import_file have no rows, so they are registered first and then imported
    (with table = "xxx_new" in the config) into the new table.
    """

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Register only the given name from the config file")

    def handle(self, config, name, *args, **kwargs):
        # Prevent overlapping runs (e.g. a slow cron run overlapping with
        # the next one). The lock is held until this command finishes, so
        # there are no stale locks. A second run fails loudly instead of
        # silently skipping.
        lockpath = settings.BASE_DIR / 'var' / 'run' / 'file_register.lock'
        lockpath.parent.mkdir(parents=True, exist_ok=True)
        with open(lockpath, 'w') as lockfile:
            try:
                fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise CommandError('another file_register run is in progress')

            with open(config, 'rb') as f:
                config = tomllib.load(f)
            config = config['import']

            for entry_name, values in config.items():
                if not isinstance(values, dict):
                    continue

                # Only entries of the new pipeline
                if values.get('pipeline', 'import_first') != 'archive_first':
                    continue

                if name and entry_name != name:
                    continue

                # Proceed
                directory = pathlib.Path(values['path'])
                if not directory.is_absolute():
                    raise CommandError(f'{entry_name}: path must be absolute: {directory}')
                pattern = values['pattern']

                archive = get_archive_root(directory, directory) / 'archive'
                if not archive.is_dir():
                    continue

                registered = existing = 0
                for path in sorted(archive.rglob('*.xz')):
                    if get_parser(path.name) is None:
                        self.stderr.write(f"{path} WARNING no parser for this file, skipped")
                        continue

                    # Entries sharing one archive directory (e.g. Biomet and
                    # Status of the same logger) only register their own files
                    if not fnmatch.fnmatch(get_raw_name(path.name), pattern):
                        continue

                    relpath = str(path.relative_to(archive))
                    _, created = ImportFile.objects.get_or_create(
                        name=entry_name, path=relpath)
                    if created:
                        registered += 1
                    else:
                        existing += 1

                self.stdout.write(
                    f"{entry_name}: {registered} registered, {existing} already existed")

        return 0
