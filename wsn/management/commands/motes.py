# Standard Library
import re
import zipfile

import tqdm

# Django
from django.core.management.base import BaseCommand

# Project
from wsn.api import frame_to_database
from wsn.parsers import waspmote


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+',
                            help='Path to file or directory')

    def handle(self, *args, **kw):
        expr = re.compile('.*DATA/[0-9]{6}\.TXT$')

        # Parse
        frames = []
        for path in kw['paths']:
            assert zipfile.is_zipfile(path)
            self.stdout.write('Parsing %s' % path)
            with zipfile.ZipFile(path, 'r') as zf:
                names = zf.namelist()
                for name in tqdm.tqdm(names):
                    if expr.match(name):
                        with zf.open(name) as data_file:
                            for frame in waspmote.read_wasp_data(data_file):
                                frame = waspmote.data_to_json(frame)
                                frames.append(frame)

        # Sort by time
        frames.sort(key=lambda x: x['frames'][0]['time'])
        first = frames[0]['frames'][0]['time']
        last = frames[-1]['frames'][0]['time']
        assert first < last

        # Inserting
        self.stdout.write('Inserting %d frames into the database' % len(frames))
        self.stdout.write('From %s to %s' % (first, last))

        # Insert
        for frame in tqdm.tqdm(frames):
            frame_to_database(frame, update=False)
