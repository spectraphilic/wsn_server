# Standard Library
import os

# Requirements
from clickhouse_driver import Client
from django.conf import settings

# Project
from wsn.parsers.base import BaseParser


def get_column(name):
    datatype = {
        'TIMESTAMP': 'UInt32',
        'RECORD': 'UInt32',
    }.get(name, 'Float32 DEFAULT NaN')

    return f'"{name}" {datatype}'


class ClickHouse:

    def __init__(self):
        self.client = None

    def __enter__(self):
        self.client = Client(
            settings.CLICKHOUSE_HOST,
            user=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_NAME,
        )

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.disconnect()

    def execute(self, query, *args, **kwargs):
        echo = kwargs.pop('echo', None)
        if echo is not None:
            print(query)

        return self.client.execute(query, *args, **kwargs)

    def insert_rows(self, table, fields, rows):
        n = len(rows)
        if n > 0:
            fields = list(fields)
            values = []
            for row in rows:
                values.append(tuple(row[name] for name in fields))

            columns = ', '.join(f'"{name}"' for name in fields)
            self.execute(
                f'INSERT INTO {table} ({columns}) VALUES', values,
                types_check=True,
                #echo=True,
            )

        return n

    def upload(self, parser_class, file, filepath, metadata=None):
        assert issubclass(parser_class, BaseParser)
        assert metadata is None or type(metadata) is dict

        with parser_class(file) as parser:
            metadata = parser.metadata or metadata

            # Guess the table name
            dirpath, filename = os.path.split(filepath)
            dirname = os.path.basename(dirpath)
            table = f"{dirname}_{metadata['table_name']}"

            # Create the table if it does not exist
            # The Replacing engine allows to avoid duplicates. Deduplication is
            # done in the background, so there may be duplicates until the parts
            # are merged.
            self.execute(
                f"CREATE TABLE IF NOT EXISTS {table} ({get_column('TIMESTAMP')}) "
                f"ENGINE = ReplacingMergeTree() ORDER BY TIMESTAMP",
                #echo=True,
            )

            # Get the table columns
            database = settings.CLICKHOUSE_NAME
            cols = set([name for name, in self.execute(
                f"SELECT name FROM system.columns "
                f"WHERE database = '{database}' AND table = '{table}';",
                #echo=True,
            )])

            # Add new columns
            fields = set(parser.fields)
            new = fields - cols
            if new:
                actions = ', '.join(f'ADD COLUMN {get_column(name)}' for name in new)
                self.execute(f'ALTER TABLE {table} {actions};')

            rows = []
            for time, data in parser:
                data['TIMESTAMP'] = int(time.timestamp())
                rows.append(data)

            self.insert_rows(table, fields, rows)

        return metadata
