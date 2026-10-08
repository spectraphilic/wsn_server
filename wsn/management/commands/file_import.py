import fcntl
import pathlib
import tempfile
import traceback

import tomllib

# Django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

# Project
from wsn.models import ImportFile
from wsn.parsers import get_parser
from wsn.parsers.base import get_archive_root, unarchive
from wsn.parsers.schemas import Schema
from wsn.upload import upload2ch, upload2pg


class Command(BaseCommand):
    """
    Import the data of files archived by the file_archive command.

    Pending rows of the wsn_importfile table are processed: the archived file
    is extracted, parsed and its data uploaded; the row is then marked as
    done. Transient errors (e.g. the database is down, the archived file is
    missing) leave the row pending, to be retried on the next run; permanent
    errors (e.g. the archived file cannot be parsed) mark the row as error.
    """

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Import only the given name from the config file")

    def handle_row(self, obj, config):
        name = obj.name
        values = config.get(name)
        if not isinstance(values, dict) or values.get('pipeline') != 'archive':
            self.stderr.write(f"{name}:{obj.path} ERROR no matching entry in the config file, left pending")
            return

        directory = pathlib.Path(values['path'])
        if not directory.is_absolute():
            self.stderr.write(f"{name}:{obj.path} ERROR path must be absolute: {directory}")
            return

        # Locate the archived file
        archived = get_archive_root(directory, directory) / 'archive' / obj.path
        if not archived.is_file():
            # This is permanent when the file has been deleted, transient
            # when there is a filesystem problem; either way the row is left
            # pending
            self.stderr.write(f"{archived} WARNING archived file not found, left pending")
            return

        Parser = get_parser(archived.name)
        if Parser is None:
            self.stderr.write(f"{archived} ERROR no parser for this file, left pending")
            return

        schema_name = values.get('schema', 'default')
        strict = values.get('schema-strict', False)
        database = values.get('database', 'clickhouse')
        table_name = values.get('table', name)
        schema = Schema(schema_name, strict)

        with tempfile.TemporaryDirectory() as tmp:
            try:
                filepath = unarchive(archived, tmp)
                parser = Parser(filepath, schema=schema)
                metadata, fields, rows = parser.parse()
            except Exception as exc:
                self.stderr.write(f"{archived} ERROR cannot parse archived file")
                traceback.print_exc(file=self.stderr)
                obj.status = ImportFile.Status.ERROR
                obj.error = str(exc) or exc.__class__.__name__
                obj.save(update_fields=['status', 'error', 'updated_at'])
                return

            # Upload; a failure here is transient, the row is left pending
            try:
                if database == 'postgres':
                    upload2pg(table_name, metadata, fields, rows)
                else:
                    upload2ch(table_name, metadata, fields, rows, schema)
            except Exception:
                self.stderr.write(f"{archived} ERROR upload failed, left pending")
                traceback.print_exc(file=self.stderr)
                return

        obj.status = ImportFile.Status.DONE
        obj.error = ''
        obj.save(update_fields=['status', 'error', 'updated_at'])
        self.stdout.write(f"{name}:{obj.path} imported, {len(rows)} rows")

    def handle(self, config, name, *args, **kwargs):
        # Prevent overlapping runs (e.g. a slow cron run overlapping with
        # the next one). The lock is held until this command finishes, so
        # there are no stale locks. A second run fails loudly instead of
        # silently skipping.
        lockpath = settings.BASE_DIR / 'var' / 'run' / 'file_import.lock'
        lockpath.parent.mkdir(parents=True, exist_ok=True)
        with open(lockpath, 'w') as lockfile:
            try:
                fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise CommandError('another file_import run is in progress')

            with open(config, 'rb') as f:
                config = tomllib.load(f)
            config = config['import']

            objs = ImportFile.objects.filter(status=ImportFile.Status.PENDING)
            if name:
                objs = objs.filter(name=name)
            for obj in objs.iterator():
                self.handle_row(obj, config)

        return 0
