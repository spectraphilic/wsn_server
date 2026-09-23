import fnmatch
import os
import pathlib
import sys

import tomllib

# Django
from django.core.management.base import BaseCommand, CommandError

# Project
from wsn.parsers import parse_archived_date
from wsn.parsers.base import get_archive_root


QUARANTINE_SUFFIXES = ('.empty', '.truncated', '.badutf8', '.badzip')


class Command(BaseCommand):
    """
    Read-only audit: check that every file in and under the import_file input
    directories has a filename from which a date can be extracted, as required
    by the archive/<YYYY>/<MM>/ layout. Recurses into subdirectories (e.g.
    manually created year directories). Also reports the archive destination
    each file would get. Exits non-zero if any file fails the check.
    """

    help = 'Check that data filenames contain a parseable date for archival'

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Check only the given name from the config file")
        parser.add_argument('--verbose', action='store_true',
            help='Also list every OK file with its date and archive destination',
        )

    def handle(self, config, name, verbose, *args, **kwargs):
        with open(config, 'rb') as f:
            config = tomllib.load(f)
        config = config['import']

        failed = 0

        for table_name, values in config.items():
            if not isinstance(values, dict):
                continue

            if name and table_name != name:
                continue

            directory = pathlib.Path(values['path'])
            if not directory.is_absolute():
                raise CommandError(f'{table_name}: path must be absolute: {directory}')
            pattern = values['pattern']

            counts = {'input': 0, 'archived': 0, 'quarantined': 0, 'subdir': 0, 'ignored': 0}
            errors = []

            for dirpath, _, filenames in os.walk(directory):
                for name_ in sorted(filenames):
                    filepath = pathlib.Path(dirpath) / name_
                    in_root = filepath.parent == directory

                    if name_.endswith('.xz'):
                        kind = 'archived'
                    elif name_.endswith(QUARANTINE_SUFFIXES):
                        kind = 'quarantined'
                    elif in_root and fnmatch.fnmatch(name_, pattern):
                        # import_file only scans the directory itself, files
                        # in subdirectories are never imported
                        kind = 'input'
                    elif in_root:
                        kind = 'ignored'
                    else:
                        kind = 'subdir'
                    counts[kind] += 1

                    if kind in ('subdir', 'ignored'):
                        continue

                    try:
                        date = parse_archived_date(name_)
                    except ValueError as e:
                        errors.append(str(e))
                        continue

                    if verbose:
                        root = get_archive_root(filepath, directory)
                        dst = root / 'archive' / str(date.year) / f'{date.month:02d}'
                        self.stdout.write(f'OK {filepath} -> {dst}/')

            self.stdout.write(
                f'{table_name} ({directory}): '
                + ', '.join(f'{k}={v}' for k, v in counts.items())
            )
            for error in errors:
                self.stdout.write(f'FAIL {error}')
            failed += len(errors)

        if failed:
            self.stderr.write(f'{failed} file(s) with no parseable date')
            # Returning 1 would make Django's BaseCommand.write() crash (it
            # treats a non-None return as output text), so exit explicitly.
            sys.exit(1)
        return 0
