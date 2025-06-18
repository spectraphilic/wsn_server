import argparse

from django.core.management.base import BaseCommand
from tabulate import tabulate

from wsn.clickhouse import ClickHouse


def check_range(value):
    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Must be an integer (got '{value}')")

    if not (1 <= value <= 1000):
        raise argparse.ArgumentTypeError(f"Must be between 1 and 1000 (got {value})")

    return value

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=check_range, default=20)

    def handle(self, limit, *arg, **kw):
        with ClickHouse() as clickhouse:
            rows, columns = clickhouse.select('finseflux_HFData', limit=limit, with_column_types=True)
            headers = [header for header, type_ in columns]
            print(tabulate(rows, headers=headers))
