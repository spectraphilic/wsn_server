import pathlib

from wsn.parsers.base import parse_filename_date
from wsn.parsers.cr6 import CR6Parser
from wsn.parsers.licor import LicorParser
from wsn.parsers.sommer import SommerParser


PARSERS = {
    '.csv': SommerParser, # Sommer MRL-7
    '.dat': CR6Parser,
    '.ghg': LicorParser,
}


def parse_archived_date(name):
    """
    Extract the date from an archived filename (<name>.<ext>.xz), using the
    get_archive_date() of the parser for the inner suffix. Raises ValueError
    if no valid date is found.
    """
    inner = name.removesuffix('.xz')
    Parser = PARSERS.get(pathlib.Path(inner).suffix)
    if Parser is None:
        return parse_filename_date(name)
    return Parser.get_archive_date(inner)
