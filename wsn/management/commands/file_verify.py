import datetime
import time
import tomllib

# Django
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count
from django.template.defaultfilters import filesizeformat

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
    Verify a migrated table against its predecessor, before or after the
    swap.

    Before the swap the entry has table = "xxx_new" in the config and the
    tables xxx (old) and xxx_new (new) are compared. After the swap the
    config option is removed and the backup table xxx_old is compared
    against the live table xxx, for as long as the backup is kept.

    Compares the ledger status, the partition keys, the row counts (with
    FINAL, so ReplacingMergeTree duplicates are accounted for), the on-disk
    sizes (informational), the TIMESTAMP range and per-column
    min/max/sum/count over the shared numeric columns. It also prints the
    rows/bytes read (from system.query_log) by the same 31-day time-range
    query on each side (informational: pruning is what the migration buys,
    and wall-clock time is cache noise). Columns that exist on only one side (e.g.
    source_file, Pressure_kPa, the inert CH4 columns) are reported as
    skipped, not compared.

    Diffs are reported, not failed: some are expected by design, e.g.
    rows with bad timestamps that the old pipeline imported and the new
    one skips. Operational problems (missing entry, table in no
    migratable state) fail loudly.
    """

    def add_arguments(self, parser):
        parser.add_argument('config', help="Path to the TOML configuration file")
        parser.add_argument('--name', help="Verify only the given name from the config file")

    @staticmethod
    def exists(ch, table):
        database = settings.CLICKHOUSE_NAME
        return ch.execute(
            "SELECT count() FROM system.tables "
            f"WHERE database = '{database}' AND name = '{table}'"
        )[0][0] > 0

    def verify(self, name, values):
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
            # Migration phase: before the swap the entry has table =
            # "xxx_new" in the config; after the swap the config option is
            # removed and the backup table is xxx_old
            table_new = values.get('table', name)
            if table_new.endswith('_new'):
                table_old = table_new[:-len('_new')]
            elif self.exists(ch, f'{name}_old'):
                table_old, table_new = f'{name}_old', name
            else:
                raise CommandError(
                    f'{name}: config has no table = "xxx_new" and no '
                    f'{name}_old table exists; run this before the swap'
                )

            self.stdout.write(f'{table_old} (old) vs {table_new} (new)')

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
            # aggregates are conditional. Columns that are date-typed on
            # either side (e.g. TIMESTAMP as UInt32 on one side and DateTime
            # on the other) are compared as epoch seconds: it makes the two
            # types comparable and sum() is not allowed on DateTime
            numeric_cols = []
            exprs = []
            specs = []  # (column, stat), positional match with the result row
            for col in shared:
                ctype, nullable = split_type(old_cols[col])
                if not ctype.startswith(NUMERIC_PREFIXES):
                    continue
                is_float = ctype.startswith('Float')
                is_date = ctype.startswith('Date') or \
                    split_type(new_cols[col])[0].startswith('Date')
                value = f'toUInt32("{col}")' if is_date else f'"{col}"'
                if nullable:
                    cond = f'({col} IS NOT NULL)'
                    if is_float:
                        cond = f'({col} IS NOT NULL AND NOT isNaN({col}))'
                    exprs.extend([
                        f'minIf({value}, {cond})',
                        f'maxIf({value}, {cond})',
                        f'sumIf({value}, {cond})',
                        f'countIf({cond})',
                    ])
                elif is_float:
                    cond = f'NOT isNaN({col})'
                    exprs.extend([
                        f'minIf({value}, {cond})',
                        f'maxIf({value}, {cond})',
                        f'sumIf({value}, {cond})',
                        f'countIf({cond})',
                    ])
                else:
                    exprs.extend([
                        f'min({value})',
                        f'max({value})',
                        f'sum({value})',
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

            # Table sizes, informational: the new table is recompressed and
            # carries source_file, so it is not a diff
            size_query = (
                "SELECT total_bytes FROM system.tables "
                f"WHERE database = '{database}' AND name = '{{}}'"
            )
            old_size = ch.execute(size_query.format(table_old))[0][0]
            new_size = ch.execute(size_query.format(table_new))[0][0]
            fmt_size = lambda s: filesizeformat(s) if s is not None else 'unknown'
            self.stdout.write(f'Size: old={fmt_size(old_size)} new={fmt_size(new_size)}')

            # Timestamp range, compared as epoch seconds so UInt32 and
            # DateTime tables are comparable, displayed as dates
            range_query = (
                'SELECT toUInt32(min(TIMESTAMP)), toUInt32(max(TIMESTAMP)) '
                'FROM {} FINAL'
            )
            old_range = ch.execute(range_query.format(table_old))[0]
            new_range = ch.execute(range_query.format(table_new))[0]
            ok = close(old_range[0], new_range[0]) and close(old_range[1], new_range[1])
            diffs += not ok

            def fmt(ts):
                return datetime.datetime.fromtimestamp(
                    ts, tz=datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')

            self.stdout.write(
                f'Range: old={fmt(old_range[0])} .. {fmt(old_range[1])} '
                f'new={fmt(new_range[0])} .. {fmt(new_range[1])} '
                f'{"OK" if ok else "DIFF"}'
            )

            # Query cost: run the same 31-day time-range query on each
            # side and report the rows/bytes read back from
            # system.query_log. Partition pruning is what the migration's
            # monthly partitioning buys, and rows read are deterministic,
            # unlike wall-clock time (cache noise). Informational, like the
            # Size line. The window is the last 31 days of the new table,
            # the same absolute window for both sides.
            window_end = new_range[1]
            window_start = window_end - 31 * 86400

            def perf_where(cols):
                ctype, _ = split_type(cols['TIMESTAMP'])
                if ctype.startswith('Date'):
                    # Direct date compare keeps partition pruning intact;
                    # wrapping the column in a function hides it from the
                    # partition key
                    return (
                        f"TIMESTAMP >= toDateTime({window_start}, 'UTC') "
                        f"AND TIMESTAMP < toDateTime({window_end}, 'UTC')"
                    )
                return (
                    f'TIMESTAMP >= {window_start} '
                    f'AND TIMESTAMP < {window_end}'
                )

            def perf_measure(table, cols, label):
                query = (
                    f'SELECT count() FROM {table} '
                    f'WHERE {perf_where(cols)}'
                )
                query_id = f'file-verify-perf-{label}'
                ch.execute(query, query_id=query_id,
                           settings={'log_queries': 1})
                return query_id

            lookup_query = (
                'SELECT read_rows, read_bytes, query_duration_ms, '
                "ProfileEvents['SelectedParts'], "
                "ProfileEvents['SelectedMarks'] "
                'FROM system.query_log '
                "WHERE type = 'QueryFinish' "
                # %(name)s params are substituted client-side by the
                # driver; {name:Type} would reach the server literally
                'AND query_id = %(query_id)s '
                'ORDER BY query_start_time DESC LIMIT 1'
            )

            # The log flushes on a timer (default every 7.5s) and the
            # table may not exist until the first flush, so poll; the
            # ClickHouse user may not be allowed to run SYSTEM FLUSH LOGS
            qids = (perf_measure(table_old, old_cols, 'old'),
                    perf_measure(table_new, new_cols, 'new'))
            perfs = [None, None]
            perf_error = None
            for _ in range(6):
                for i, qid in enumerate(qids):
                    if perfs[i] is not None:
                        continue
                    try:
                        rows = ch.execute(lookup_query, {'query_id': qid})
                        perfs[i] = rows[0] if rows else None
                    except Exception as exc:
                        perf_error = exc
                if all(p is not None for p in perfs):
                    break
                time.sleep(2)

            old_perf, new_perf = perfs
            if any(p is None for p in perfs) and perf_error is None:
                perf_error = RuntimeError(
                    'no query_log entry for the measured queries')

            def fmt_perf(perf):
                if perf is None:
                    return 'unavailable'
                rows, bytes_, ms, parts, marks = perf
                return (
                    f'{rows:,} rows, {filesizeformat(bytes_)} '
                    f'in {ms} ms ({parts} parts, {marks} marks)'
                )

            perf_line = (
                f'Perf: {fmt(window_start)} .. {fmt(window_end)}: '
                f'old={fmt_perf(old_perf)} new={fmt_perf(new_perf)}'
            )
            if perf_error is not None:
                reason = str(perf_error).splitlines()[0]
                perf_line += f' ({type(perf_error).__name__}: {reason})'
            self.stdout.write(perf_line)

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

        # Batch mode only: the set of existing tables, to skip entries that
        # are in no migratable state (no xxx_new in the config, no xxx_old
        # in ClickHouse)
        existing = set()
        if not name:
            with ClickHouse() as ch:
                database = settings.CLICKHOUSE_NAME
                existing = {row[0] for row in ch.execute(
                    f"SELECT name FROM system.tables "
                    f"WHERE database = '{database}'")}

        for entry_name, values in config.items():
            if not isinstance(values, dict):
                continue
            if values.get('pipeline', 'import_first') != 'archive_first':
                continue
            if name:
                if entry_name != name:
                    continue
            elif not (values.get('table', entry_name).endswith('_new')
                      or f'{entry_name}_old' in existing):
                continue
            verified += 1
            diffs, p = self.verify(entry_name, values)
            total_diffs += diffs
            problems += p

        if name and not verified:
            raise CommandError(f'{name}: no archive_first entry found in the config')

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
