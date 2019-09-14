# Requirements
from clickhouse_driver import Client
from django.conf import settings


def get_column(name):
    datatype = {
        'TIMESTAMP': 'UInt32',
        'RECORD': 'UInt32',
    }.get(name, 'Float64 DEFAULT NaN')

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

    def upload(self, name, metadata, fields, rows):
        rows2 = []
        for time, data in rows:
            data = data.copy()
            data['TIMESTAMP'] = int(time.timestamp())
            rows2.append(data)
        rows = rows2

        # Guess the table name
        table = f"{name}_{metadata['table_name']}"

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
        fields = set(fields)
        new = fields - cols
        if new:
            actions = ', '.join(f'ADD COLUMN {get_column(name)}' for name in new)
            self.execute(f'ALTER TABLE {table} {actions};')

        self.insert_rows(table, fields, rows)

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
            if value is not None:
                query.append(fstr.format(value))

        query = ' '.join(query)
        return self.execute(query, **kwargs)
