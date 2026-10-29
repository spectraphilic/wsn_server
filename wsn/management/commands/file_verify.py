import tomllib

# Django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count

# Project
from wsn.clickhouse import ClickHouse
from wsn.models import ImportFile


# What ClickHouse.upload() creates (wsn/clickhouse.py)
EXPECTED_PARTITION_KEY = 'toYYYYMM(toDateTime(TIMESTAMP))'


NUMERIC_PREFIXES = ('Int', 'UInt', 'Float', 'Decimal')
STATS = ('min', 'max', 'sum', 'count')


def split_type(ctype):
    """Split a ClickHouse type into (inner type, is_nullable)."""
    nullable = ctype.startswith('Nullable(')
    if nullable:
        ctype = ctype[len('Nullable('):-1]
    return ctype, nullable


def close(old, new):
    """
    Compare two aggregate values: floats with tolerance (sums vary with
    part layout between two tables), everything else exactly.
    """
    if old is None or new is None:
        return old is new
    if isinstance(old, float) or isinstance(new, float):
        try:
            old, new = float(old), float(new)
        except (TypeError, ValueError):
            return False
        return abs(old - new) <= 1e-9 * max(1.0, abs(old), abs(new))
    return old == new


class Command(BaseCommand):
    """
    Verify a migrated table against its predecessor, before the swap.

    Runs against entries that still have table = "xxx_new" in the config.
    Compares the ledger status, the partition keys, the row counts (with
    FINAL, so ReplacingMergeTree duplicates are accounted for), the
    TIMESTAMP range and per-column min/max/sum/count over the shared
    numeric columns. Columns that exist on only one side (e.g.
    source_file, Pressure_kPa, the inert CH4 columns) are reported as
    skipped, not compared.

    Diffs are reported, not failed: some are expected by design, e.g.
    rows with bad timestamps that the old pipeline imported and the new
    one skips. Operational problems (missing entry, table not *_new)
    fail loudly.
    """

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Verify only the given name from the config file")

    def verify(self, name, values):
        table_new = values.get('table', name)
        if not table_new.endswith('_new'):
            raise CommandError(
                f'{name}: config table = "{table_new}" is not a *_new table; '
                'run this before the swap'
            )
        table_old = table_new[:-len('_new')]

        self.stdout.write(f'{table_old} (old) vs {table_new} (new)')

        # Ledger
        rows = ImportFile.objects.filter(name=name).values('status').annotate(n=Count('status'))
        status = {row['status']: row['n'] for row in rows}
        pending = status.get('pending', 0)
        error = status.get('error', 0)
        self.stdout.write(
            f"Ledger: {status.get('done', 0)} done, {pending} pending, {error} error"
        )
        problems = pending + error

        diffs = 0
        with ClickHouse() as ch:
            def columns(table):
                try:
                    return {row[0]: row[1] for row in ch.execute(f'DESCRIBE TABLE {table}')}
                except Exception as exc:
                    raise CommandError(f'cannot describe table {table}: {exc}')

            old_cols = columns(table_old)
            new_cols = columns(table_new)

            shared = sorted(set(old_cols) & set(new_cols))
            only_old = sorted(set(old_cols) - set(new_cols))
            only_new = sorted(set(new_cols) - set(old_cols))
            self.stdout.write(
                f'Columns: {len(shared)} shared'
                + (f', only in old: {", ".join(only_old)}' if only_old else '')
                + (f', only in new: {", ".join(only_new)}' if only_new else '')
            )
            # Type changes on shared columns (e.g. RECORD -> Nullable) are
            # expected on some tables; reported, like the one-sided columns
            type_diffs = sorted(
                f'{col} ({old_cols[col]} -> {new_cols[col]})'
                for col in shared
                if old_cols[col] != new_cols[col]
            )
            if type_diffs:
                self.stdout.write(f'Types differ: {", ".join(type_diffs)}')

            # Partitioning: monthly partitioning is a goal of the migration,
            # so the new table must carry the expected partition key (the
            # old one is displayed for the record; a few old tables like
            # myr1_HFData_sonic are already partitioned)
            database = settings.CLICKHOUSE_NAME
            partition_query = (
                "SELECT partition_key FROM system.tables "
                f"WHERE database = '{database}' AND name = '{{}}'"
            )
            old_part = ch.execute(partition_query.format(table_old))[0][0]
            new_part = ch.execute(partition_query.format(table_new))[0][0]
            ok = new_part == EXPECTED_PARTITION_KEY
            diffs += not ok
            self.stdout.write(
                f'Partition: old={old_part or "(none)"} new={new_part or "(none)"} '
                f'{"OK" if ok else f"DIFF (expected {EXPECTED_PARTITION_KEY})"}'
            )

            # One aggregate query per table over the shared numeric columns;
            # Float columns default to NaN and RECORD is nullable, so the
            # aggregates are conditional
            numeric_cols = []
            exprs = []
            specs = []  # (column, stat), positional match with the result row
            for col in shared:
                ctype, nullable = split_type(old_cols[col])
                if not ctype.startswith(NUMERIC_PREFIXES):
                    continue
                is_float = ctype.startswith('Float')
                if nullable:
                    cond = f'({col} IS NOT NULL)'
                    if is_float:
                        cond = f'({col} IS NOT NULL AND NOT isNaN({col}))'
                    exprs.extend([
                        f'minIf("{col}", {cond})',
                        f'maxIf("{col}", {cond})',
                        f'sumIf("{col}", {cond})',
                        f'countIf({cond})',
                    ])
                elif is_float:
                    cond = f'NOT isNaN({col})'
                    exprs.extend([
                        f'minIf("{col}", {cond})',
                        f'maxIf("{col}", {cond})',
                        f'sumIf("{col}", {cond})',
                        f'countIf({cond})',
                    ])
                else:
                    exprs.extend([
                        f'min("{col}")',
                        f'max("{col}")',
                        f'sum("{col}")',
                        f'count("{col}")',
                    ])
                numeric_cols.append(col)
                specs.extend((col, stat) for stat in STATS)

            def stats(table):
                row = ch.execute(f'SELECT {", ".join(exprs)} FROM {table} FINAL')[0]
                return dict(zip(specs, row))

            # Row counts
            old_count = ch.execute(f'SELECT count() FROM {table_old} FINAL')[0][0]
            new_count = ch.execute(f'SELECT count() FROM {table_new} FINAL')[0][0]
            ok = close(old_count, new_count)
            diffs += not ok
            self.stdout.write(f'Rows: old={old_count} new={new_count} {"OK" if ok else "DIFF"}')

            # Timestamp range
            range_query = 'SELECT min(TIMESTAMP), max(TIMESTAMP) FROM {} FINAL'
            old_range = ch.execute(range_query.format(table_old))[0]
            new_range = ch.execute(range_query.format(table_new))[0]
            ok = close(old_range[0], new_range[0]) and close(old_range[1], new_range[1])
            diffs += not ok
            self.stdout.write(
                f'Range: old={old_range[0]} .. {old_range[1]} '
                f'new={new_range[0]} .. {new_range[1]} {"OK" if ok else "DIFF"}'
            )

            # Per-column aggregates
            old_stats = stats(table_old)
            new_stats = stats(table_new)
            for col in numeric_cols:
                parts = []
                for stat in STATS:
                    old, new = old_stats[(col, stat)], new_stats[(col, stat)]
                    if not close(old, new):
                        parts.append(f'{stat} old={old} new={new}')
                if parts:
                    diffs += 1
                    self.stdout.write(f'{col}: DIFF {"; ".join(parts)}')
                else:
                    self.stdout.write(f'{col}: OK')

        return diffs, problems

    def handle(self, config, name, *args, **kwargs):
        with open(config, 'rb') as f:
            config = tomllib.load(f)
        config = config['import']

        verified = 0
        total_diffs = 0
        problems = 0
        for entry_name, values in config.items():
            if not isinstance(values, dict):
                continue
            if values.get('pipeline', 'import_first') != 'archive_first':
                continue
            if name:
                if entry_name != name:
                    continue
            elif not values.get('table', entry_name).endswith('_new'):
                # Batch mode: already-swapped entries are skipped silently
                continue
            verified += 1
            diffs, p = self.verify(entry_name, values)
            total_diffs += diffs
            problems += p

        if name and not verified:
            raise CommandError(
                f'{name}: no archive_first entry with table = "xxx_new" found in the config'
            )

        if problems:
            self.stderr.write(
                'Ledger has pending/error rows — resolve them before the swap'
            )
        if total_diffs:
            self.stdout.write(
                f'{total_diffs} check(s) differ — review; bad-timestamp rows skipped by '
                'the new pipeline are an expected diff on some tables'
            )
        else:
            self.stdout.write('All checks OK')

        return 0
