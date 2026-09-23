import os
import pathlib

import tomllib

# Django
from django.core.management.base import BaseCommand, CommandError

# Project
from wsn.parsers import parse_archived_date
from wsn.parsers.base import get_archive_root


class Command(BaseCommand):
    """
    Move already-archived (*.xz) files into the archive/<YYYY>/<MM>/ layout,
    by the date in the filename. Recurses into subdirectories (e.g. manually
    created year directories) but never touches files already under archive/.
    Files with no parseable date are reported and skipped. Dry run by default,
    use --apply to actually move the files.
    """

    help = 'Move archived (*.xz) files into the archive/<YYYY>/<MM>/ layout'

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Migrate only the given name from the config file")
        parser.add_argument('--apply', action='store_true',
            help='Actually move the files (default is a dry run)',
        )

    def handle(self, config, name, apply, *args, **kwargs):
        with open(config, 'rb') as f:
            config = tomllib.load(f)
        config = config['import']

        if not apply:
            self.stdout.write('DRY RUN (use --apply to move the files)')

        # Several config entries can share the same directory (e.g. the
        # finseflux Biomet/StationStatus/HFData tables), process each
        # directory only once.
        directories = []
        for table_name, values in config.items():
            if not isinstance(values, dict):
                continue

            if name and table_name != name:
                continue

            directory = pathlib.Path(values['path'])
            if not directory.is_absolute():
                raise CommandError(f'{table_name}: path must be absolute: {directory}')

            if directory not in directories:
                directories.append(directory)

        for directory in directories:
            self.handle_directory(directory, apply)

    def handle_directory(self, directory, apply):
        moved = skipped = 0
        errors = []

        for dirpath, _, filenames in os.walk(directory):
            for name_ in sorted(filenames):
                filepath = pathlib.Path(dirpath) / name_

                if not name_.endswith('.xz'):
                    continue

                root = get_archive_root(filepath, directory)
                archive_dir = root / 'archive'

                # Already in the right place
                if filepath.is_relative_to(archive_dir):
                    continue

                try:
                    date = parse_archived_date(name_)
                except ValueError as e:
                    errors.append(str(e))
                    continue

                dst = archive_dir / str(date.year) / f'{date.month:02d}' / name_

                if dst.exists():
                    self.stdout.write(f'SKIP {filepath} (already exists: {dst})')
                    skipped += 1
                    continue

                if apply:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    os.rename(filepath, dst)
                    moved += 1
                else:
                    self.stdout.write(f'WOULD MOVE {filepath} -> {dst}')

        if apply:
            # Remove the now-empty directories left behind (e.g. the old
            # manually created year directories)
            for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
                if pathlib.Path(dirpath) == directory:
                    continue
                if not dirnames and not filenames:
                    os.rmdir(dirpath)

        self.stdout.write(f'{directory}: moved={moved}, skipped={skipped}')
        for error in errors:
            self.stdout.write(f'FAIL {error}')
