# Standard Library
import lzma
import os

# Django
from django.conf import settings

# App
from wsn.clickhouse import ClickHouse
from wsn.models import Metadata, Frame


ARCHIVE = os.path.join(settings.BASE_DIR, 'var', 'archive')


# Mapping to load the metadata with a different name
METADATA_NAMES = {
    'CR6 Austfonna': 'UIO_Iridium_CR6',
    'CR1000 Austfonna': 'UIO_Iridium_CR6',
}


def upload2pg(name, metadata, fields, rows):
    """
    The metadata may be provided externally, as some files don't include
    metadata.
    """
    # Use a different metadata name
    metadata_name = metadata['name']
    metadata_name = METADATA_NAMES.get(metadata_name, metadata_name)
    metadata['name'] = metadata_name

    # Load
    metadata, created = Metadata.get_or_create(metadata)
    for t, data in rows:
        Frame.create(metadata, t, None, data, update=False)

    return metadata


def upload2ch(name, metadata, fields, rows):
    if len(rows) > 0:
        with ClickHouse() as clickhouse:
            clickhouse.upload(name, metadata, fields, rows)


def archive(name, filename, data):
    # Create parent dirs
    dirpath = os.path.join(ARCHIVE, name)
    os.makedirs(dirpath, exist_ok=True)

    # Compress and save file
    filepath = os.path.join(dirpath, filename) + '.xz'
    with lzma.open(filepath, 'w') as f:
        f.write(data)
