import datetime
from types import SimpleNamespace

from ch import admin as ch_admin
from ch.models_unmanaged import GruvebadetDiagnostic

ADMIN = ch_admin.make_readonly_admin_with_formatted_timestamp(GruvebadetDiagnostic)


def formatted(value):
    model_admin = ADMIN(GruvebadetDiagnostic, ch_admin.admin.site)
    obj = SimpleNamespace(timestamp=value)
    return model_admin.formatted_timestamp(obj)


def test_formatted_timestamp_epoch_seconds():
    # 1700000000 is 2023-11-14 22:13:20 UTC
    assert formatted(1700000000) == '2023-11-14 22:13:20'


def test_formatted_timestamp_epoch_milliseconds():
    assert formatted(1700000000000) == '2023-11-14 22:13:20'


def test_formatted_timestamp_datetime():
    # What clickhouse-driver returns for a DateTime('UTC') column
    dt = datetime.datetime(2023, 11, 14, 22, 13, 20, tzinfo=datetime.UTC)
    assert formatted(dt) == '2023-11-14 22:13:20'


def test_formatted_timestamp_none():
    assert formatted(None) is None
