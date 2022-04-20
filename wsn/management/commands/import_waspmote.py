# Standard Library
import contextlib
from datetime import datetime
import pathlib
import re
from time import time
import zipfile

# Requirements
import tqdm

# Django
from django.core.management.base import BaseCommand

# Project
from wsn.models import frame_to_database
from wsn.parsers import waspmote
from wsn.settings import WSN_MIN_DATE


# TODO Replace the code below with zipfile.Path (after migration to Python 3.8)
class Directory:

    def __init__(self, path):
        self.path = path

    def namelist(self):
        return [str(x.relative_to(self.path)) for x in self.path.rglob('*')]

    def open(self, name):
        return open(self.path / name, 'rb')

@contextlib.contextmanager
def opencontainer(path):
    path = pathlib.Path(path)

    if path.is_dir():
        yield Directory(path)
    elif zipfile.is_zipfile(path):
        f = zipfile.ZipFile(path)
        yield f
        f.close()
    else:
        raise ValueError(f'{path} is not a directory nor a zip file')


class Command(BaseCommand):

    def add_arguments(self, parser):
        add_argument = parser.add_argument
        add_argument('paths', nargs='+', help='Path to file or directory')
        add_argument('--merge', action='store_true', default=False,
                     help='Merge split frames (for xbee, where pkg size is too small)')

    def handle(self, paths, merge, *args, **kw):
        expr = re.compile(r'.*DATA/([0-9]{6})\.TXT$')

        series = {}
        state = {}

        # Parse
        skipped = []
        for path in paths:
            self.stdout.write(f'Parsing {path}')
            with opencontainer(path) as container:
                names = sorted(container.namelist())
                for name in tqdm.tqdm(names):
                    match = expr.match(name)
                    if match:
                        date = '20' + match.group(1)
                        try:
                            date = datetime.strptime(date, '%Y%m%d').date()
                        except ValueError:
                            # Skip the 000000.TXT file, anyway the data it
                            # contains will have a bad timestamp, since this
                            # happens when there's an error in the I2C bus.
                            skipped.append(name)
                            continue

                        if date < WSN_MIN_DATE.date():
                            skipped.append(name)
                            continue

                        with container.open(name) as data_file:
                            for frame in waspmote.read_wasp_data(data_file):
                                # Add name to frame if it's missing
                                serial = frame['serial']
                                name = frame['name']
                                if serial not in state or frame['name']:
                                    state[serial] = name
                                else:
                                    name = frame['name'] = state[serial]

                                # Preprocess frame, changes from flat structure
                                # to {'tags': {}, 'frames': []} structure
                                frame = waspmote.data_to_json(frame)

                                # Append frame to series
                                key = (serial, name)
                                if key not in series:
                                    series[key] = frame
                                else:
                                    series[key]['frames'].extend(frame['frames'])


        # Skipped data files
        if skipped:
            self.stdout.write('Data files skipped: %s' % skipped)

        # Import series
        for serie in series.values():
            tags = serie['tags']
            frames = serie['frames']
            n = len(frames)

            # Sort by time
            #frames.sort(key=lambda x: x['time'])

            # Print
            self.stdout.write('')
            self.stdout.write('serial={serial} name={name}'.format(**tags))
            first = frames[0]['time']
            if n > 1:
                last = frames[-1]['time']
                assert first < last
                first = datetime.utcfromtimestamp(first)
                last = datetime.utcfromtimestamp(last)
                self.stdout.write('{} frames from {} to {}'.format(n, first, last))
            else:
                first = datetime.utcfromtimestamp(first)
                self.stdout.write('{} frame at {}'.format(n, first))

            # Inserting
            yes = input('Insert into database? Yes/[No]: ')
            if yes.lower() == 'yes':
                t0 = time()
                frame_to_database(serie, update=False, merge=merge)
                self.stdout.write('Done in 5{} seconds'.format(time() - t0))
