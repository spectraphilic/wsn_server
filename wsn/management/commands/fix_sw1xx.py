# Standard Library
import collections
from datetime import datetime
from decimal import Decimal
import logging
from pathlib import Path

# Django
from django.core.management.base import BaseCommand
from django.db import transaction

# Project
from wsn.models import Frame
from wsn.parsers import waspmote


logger = logging.getLogger(__name__)

Line = collections.namedtuple('Line', ['lineno', 'time', 'line', 'tail'])

def startswith(tail, prefixes):
    for prefix in prefixes:
        if tail.startswith(prefix):
            return True

    return False


class DataIterator:
    def __init__(self, path):
        self.iterators = {}
        for path in sorted(path.iterdir()):
            if path.suffix == '.TXT':
                data_file = path.open('rb')
                self.iterators[path.stem] = waspmote.read_wasp_data(data_file)

    def next(self, name):
        return next(self.iterators[name])


class Command(BaseCommand):

    def add_arguments(self, parser):
        add_argument = parser.add_argument
        add_argument('path', help='Path to SD directory')
        add_argument('--save', action='store_true', default=False)

    def print_line(self, *args):
        line = [x.decode() if type(x) is bytes else str(x) for x in args]
        self.stdout.write(' '.join(line))

    def __get_frame(self, data):
        name = data['name']
        if name not in self.frames:
            self.frames[name] = Frame.objects.filter(metadata__name=name)

        frames = self.frames[name]
        return frames.get(time=data['tst'], frame=data['frame'])

    def __fix_time(self, logfile, data_iterator):
        self.frames = {}

        prefixes = [
            b'INFO Welcome to wsn',
            b'INFO ===== Loop ',
        ]

        lora = False
#       gps_time = None
        max_time = None
        ref = None

        prev = Line(0, 0.0, b'\n', b'')
        for lineno, line in enumerate(logfile, start=1):
            time, tail = line.split(b' ', 1)
            time = float(time)

            if startswith(tail, [b'INFO LoRa started']):
                lora = True
            elif startswith(tail, [b'INFO LoRa stopped', b'INFO Welcome to wsn', b'INFO ===== Loop ']):
                lora = False

#           if startswith(tail, [b'INFO GPS Time updated!']):
#               gps_time = time
#               if gps_time < max_time:
#                   logger.warning(f'{lineno}: Bad GPS time {gps_time} {max_time} {max_time - gps_time}')

            if startswith(tail, [b'INFO Time loaded from TIME.TXT']):
                logger.warning(f'{lineno}: Time restored from TIME.TXT')
                delta = 0
            elif time < prev.time and (prev.time - time) > 60:
                delta = float(Decimal(str(prev.time)) - Decimal(str(time)))
                logger.warning(f'{lineno}: Back in time {delta}')

            if startswith(tail, prefixes):
                ref = Line(lineno, time, line, tail)
                ref_time = int(ref.time)
                fixed_time = None
                if max_time is None:
                    max_time = ref_time
                elif ref_time > max_time:
#                   if (ref_time - max_time) > 2401:
#                       logger.warning(f'{lineno} {ref_time - max_time}')
                    max_time = ref_time
                else:
                    fixed_time = ref_time + delta
#                   logger.warning(f'!! {lineno}: {ref_time} {max_time} {fixed_time} {fixed_time - max_time}')
#                   ref_time += delta
            elif tail.startswith(b'INFO Frame saved to') and not lora:
                # May happen if log file is truncated for some reason (e.g.
                # happens with sw-110)
                if ref is None:
                    continue

#               self.print_line(ref.lineno, ref.line)
#               self.print_line(lineno, line)

                # Get data from data file
                date = datetime.utcfromtimestamp(time).strftime('%y%m%d')
                data = data_iterator.next(date)
#               self.stdout.write(data)
                if not prev.tail.startswith(b'INFO Welcome to wsn'):
                    # This may happen if the log file is truncated for some
                    # reason, then there may be frames in the data files not
                    # in the log file.
                    while data['tst'] < ref_time:
                        data = data_iterator.next(date)

                    if data['tst'] != ref_time:
                        logger.error(f'{lineno}: log-time={ref_time} data-time={data["tst"]}')
                        break

                # Get frame from database
                if fixed_time is not None:
                    frame = self.__get_frame(data)
                    self.stdout.write(f'pk={frame.id} time={ref_time} fixed={fixed_time}')
                    frame.time = fixed_time
                    frame.save()

#               frame = self.__get_frame(data)
#               self.stdout.write(f'pk = {frame.id}')
#               self.stdout.write()

            prev = Line(lineno, time, line, tail)

    def fix_time(self, path):
        path = Path(path)
        data_iterator = DataIterator(path / 'DATA')
        with (path / 'LOG.TXT').open('rb') as file:
            self.__fix_time(file, data_iterator)

    def handle(self, path, save, *args, **kw):
        if not save:
            logger.info('The changes will not be saved')

        abort_message = 'Abort the transaction'
        try:
            with transaction.atomic():
                self.fix_time(path)

                # Raise an exception to abort the transaction
                if not save:
                    raise RuntimeError(abort_message)
        except RuntimeError as excp:
            if str(excp) != abort_message: # This was unexpected
                raise

            logger.info(abort_message)
