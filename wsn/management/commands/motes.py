# Standard Library
from datetime import datetime
import re
from time import time
import zipfile

import tqdm

# Django
from django.core.management.base import BaseCommand

# Project
from wsn.api import frame_to_database
from wsn.parsers import waspmote
from wsn.settings import WSN_MIN_DATE


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+',
                            help='Path to file or directory')

    def handle(self, *args, **kw):
        expr = re.compile(r'.*DATA/([0-9]{6})\.TXT$')

        series = {}
        state = {}

        # Parse
        skipped = []
        for path in kw['paths']:
            assert zipfile.is_zipfile(path)
            self.stdout.write('Parsing %s' % path)
            with zipfile.ZipFile(path, 'r') as zf:
                names = sorted(zf.namelist())
                for name in tqdm.tqdm(names):
                    match = expr.match(name)
                    if match:
                        date = '20' + match.group(1)
                        date = datetime.strptime(date, '%Y%m%d').date()
                        if date < WSN_MIN_DATE.date():
                            skipped.append(name)
                            continue

                        with zf.open(name) as data_file:
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

                                # Discard bad frames (TODO)
#                               time = frame['frames'][0]['time']
#                               time = datetime.strptime(time, '%Y-%m-%dT%H:%M:%S+00:00')
#                               if time.date() != date:
#                                   print(name)
#                                   print(frame)
#                                   continue

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

            # Sort by time
            #frames.sort(key=lambda x: x['time'])
            first = frames[0]['time']
            last = frames[-1]['time']
            assert first < last

            # Inserting
            self.stdout.write('')
            self.stdout.write('serial={serial} name={name}'.format(**tags))
            self.stdout.write('{} frames from {} to {}'.format(len(frames), first, last))
            yes = input('Insert into database? Yes/[No]: ')
            if yes.lower() == 'yes':
                t0 = time()
                frame_to_database(serie, update=False)
                self.stdout.write('Done in 5{} seconds'.format(time() - t0))
