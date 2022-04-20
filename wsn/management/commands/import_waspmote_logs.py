# Standard Library
import collections
from decimal import Decimal
import itertools
import logging
from pathlib import Path

# Django
from django.core.management.base import BaseCommand
from django.db import transaction

# Project
from wsn.models import Frame
from wsn.parsers import waspmote
from wsn import utils


logger = logging.getLogger(__name__)

Line = collections.namedtuple('Line', ['lineno', 'time', 'line', 'tail'])

def startswith(tail, prefixes):
    for prefix in prefixes:
        if tail.startswith(prefix):
            return True

    return False


class DataIterator:
    def __init__(self, path):
        self.frames = {}
        for path in sorted(path.iterdir()):
            if path.suffix == '.TXT':
                data_file = path.open('rb')
                for frame in waspmote.read_wasp_data(data_file):
                    time = frame['tst']
                    self.frames.setdefault(time, []).append(frame)

    def next(self, time, lineno):
        time = int(time)

        frames = self.frames
        if time not in frames:
            logger.warning(f'{lineno}: frame time={time} not found in data files')
            return None

        frame = frames[time].pop(0)
        if not frames[time]:
            del frames[time]
        return frame


class Command(BaseCommand):

    def add_arguments(self, parser):
        add_argument = parser.add_argument
        add_argument('path', help='Path to SD directory')
        add_argument('--save', action='store_true', default=False)
        add_argument('--fix', action='store_true', default=False,
                     help='Fix frames in the database instead of importing')

    def print_line(self, *args):
        line = [x.decode() if type(x) is bytes else str(x) for x in args]
        self.stdout.write(' '.join(line))

    def __get_frame(self, data):
        name = data['name']
        if name not in self.frames:
            self.frames[name] = Frame.objects.filter(metadata__name=name)

        frames = self.frames[name]
        try:
            return frames.get(time=data['tst'], frame=data['frame'])
        except Frame.DoesNotExist:
            return None

    def __fix_time(self, logfile, data_iterator, fix):
        self.frames = {}

        prefixes = [
            b'INFO Welcome to wsn',
            b'INFO ===== Loop ',
            b'INFO ping() ...', # rssimap
        ]

        lora = False
#       gps_time = None
        max_time = None
        ref = None

        series = {}
        # series: {(serial, name): <serie>}
        # serie: {tags: {serial: , name:}, frames: [{time: data: {} ...}]}
        prev = Line(0, 0.0, b'\n', b'')
        for lineno, line in enumerate(logfile, start=1):
            if b' ' not in line:
                continue

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
                elif delta:
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
                data = data_iterator.next(ref_time, lineno)
                if data is not None:
                    # Get frame from database
                    if fix is False:
                        frame = self.__get_frame(data)
                        if frame is None:
                            if fixed_time is not None:
                                data['tst'] = int(fixed_time)
                            frame = waspmote.data_to_json(data)
                            # Append frame to series
                            serial = frame['tags']['serial']
                            name = frame['tags']['name']
                            key = (serial, name)
                            if key not in series:
                                series[key] = frame
                            else:
                                series[key]['frames'].extend(frame['frames'])
                    elif fixed_time is not None:
                        frame = self.__get_frame(data)
                        assert frame is not None
                        self.stdout.write(f'pk={frame.id} time={ref_time} fixed={fixed_time}')
                        frame.time = fixed_time
                        frame.save()

            prev = Line(lineno, time, line, tail)

        # Import
        if fix is False:
            utils.import_waspmote_series(series, self.stdout, merge=False)

    def __handle(self, path, fix):
        path = Path(path)
        data_iterator = DataIterator(path / 'DATA')
        with (path / 'LOG.TXT').open('rb') as file:
            self.__fix_time(file, data_iterator, fix)

        return data_iterator.frames

    def handle(self, path, save, fix, *args, **kwargs):
        if not save:
            logger.info('The changes will not be saved')

        abort_message = 'Abort the transaction'
        try:
            with transaction.atomic():
                frames = self.__handle(path, fix)

                # Raise an exception to abort the transaction
                if not save:
                    raise RuntimeError(abort_message)
        except RuntimeError as excp:
            if str(excp) != abort_message: # This was unexpected
                raise

            logger.info(abort_message)

        if frames:
            print('Frames not in the log file:')
            print(list(itertools.chain(*frames.values())))
