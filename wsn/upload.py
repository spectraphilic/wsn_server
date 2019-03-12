# Standard Library
import lzma
import os

# Django
from django.conf import settings

# App
from wsn.models import Metadata, Frame
from wsn.parsers.base import BaseParser


ARCHIVE = os.path.join(settings.BASE_DIR, 'var', 'archive')


def upload(parser_class, file, filename=None, metadata=None):
    """
    The metadata may be provided externally, as some files don't include
    metadata.
    """
    assert issubclass(parser_class, BaseParser)
    assert metadata is None or type(metadata) is dict

    with parser_class(file) as parser:
        metadata = parser.metadata or metadata
        metadata, created = Metadata.get_or_create(metadata)
        for time, data in parser:
            Frame.create(metadata, time, None, data, update=False)

    return metadata


def archive(name, filename, data):
    # Create parent dirs
    dirpath = os.path.join(ARCHIVE, name)
    os.makedirs(dirpath, exist_ok=True)

    # Compress and save file
    filepath = os.path.join(dirpath, filename) + '.xz'
    with lzma.open(filepath, 'w') as f:
        f.write(data)
