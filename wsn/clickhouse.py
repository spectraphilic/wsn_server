import datetime

# Requirements
from clickhouse_driver import Client
from django.conf import settings

# Project
from wsn.parsers.cr6 import parse_datetime


def get_column(name, schema=None):
    field = schema.get_field(name)
    if field is None:
        raise ValueError(f"Field '{name}' not found in schema")
    return f'"{name}" {field.type}'


def get_value(schema, name, value):
    field = schema.get_field(name)
    if field is None:
        return None  # Skip unknown fields in strict mode

    datatype = field.type
    if datatype is None:
        return value
    elif datatype.startswith('DateTime64'):
        return parse_datetime(value)
    elif datatype.startswith('DateTime'):
        value = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        return value.replace(tzinfo=datetime.UTC)

    return value

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

    def upload(self, table_name, metadata, fields, rows, schema=None,
               source_file=None):
        assert schema is not None

        rows2 = []
        for time, data in rows:
            processed_data = {}
            for key, value in data.items():
                processed_value = get_value(schema, key, value)
                if processed_value is not None:
                    processed_data[key] = processed_value
            data = processed_data

            # Time
            key = 'TIMESTAMP'
            value = time
            field = schema.get_field(key)
            if field is None:
                raise ValueError("TIMESTAMP field not found in schema")
            if field.type == 'UInt32':
                value = int(time.timestamp())
            data[key] = value

            # The archive file this row was parsed from, so rows can be
            # traced back to their source; the same archive-relative path
            # is used by the wsn_importfile ledger. Not a schema field, the
            # import pipeline provides it.
            if source_file is not None:
                data['source_file'] = source_file

            rows2.append(data)
        rows = rows2

        # Create the table if it does not exist
        # The Replacing engine allows to avoid duplicates. Deduplication is
        # done in the background, so there may be duplicates until the parts
        # are merged.
        # Partitioned by month, hardcoded: time-range queries skip whole
        # months, and a month can be dropped and re-imported cheaply
        # (DROP PARTITION instead of a heavy DELETE mutation). toDateTime
        # because TIMESTAMP may be UInt32 (epoch) instead of a date type.
        column = get_column('TIMESTAMP', schema)
        self.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} ({column}) "
            f"ENGINE = ReplacingMergeTree() "
            f"PARTITION BY toYYYYMM(toDateTime(TIMESTAMP)) "
            f"ORDER BY TIMESTAMP",
            #echo=True,
        )

        # Get the table columns
        database = settings.CLICKHOUSE_NAME
        cols = set([name for name, in self.execute(
            f"SELECT name FROM system.columns "
            f"WHERE database = '{database}' AND table = '{table_name}';",
            #echo=True,
        )])

        # Add new columns
        fields = set(fields)
        if source_file is not None:
            fields.add('source_file')
        new = fields - cols
        if new:
            actions = []
            for name in new:
                if name == 'source_file':
                    # Pipeline-provided, not a schema field
                    actions.append('ADD COLUMN source_file LowCardinality(String)')
                else:
                    actions.append(f'ADD COLUMN {get_column(name, schema)}')
            self.execute(f"ALTER TABLE {table_name} {', '.join(actions)};")

        self.insert_rows(table_name, fields, rows)

        return metadata


    def select(self, table, columns=None, where=None, group_by=None,
               order_by=None, limit=None, limit_by=None, **kwargs):

        if not columns:
            columns = '*'
        else:
            assert type(columns) is list
            columns = ', '.join(columns)

        query = [f'SELECT {columns} FROM {table}']

        clauses = [
            ('WHERE {}', where),
            ('GROUP BY {}', group_by),
            ('ORDER BY {}', order_by),
            ('LIMIT {0[0]} BY {0[1]}', limit_by),
            ('LIMIT {}', limit),
        ]
        for fstr, value in clauses:
            if value not in (None, ''):
                query.append(fstr.format(value))

        query = ' '.join(query)
        return self.execute(query, **kwargs)
