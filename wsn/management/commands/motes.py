# Standard Library
from datetime import datetime, timezone
import zipfile

import tqdm

# Django
from django.core.management.base import BaseCommand

# Project
from wsn.models import Frame, Metadata
from wsn.parsers.waspmote import read_wasp_data


def data_to_json(data):
    """
    Adapt the data to the structure expected by Django.
    """
    # Tags
    tags = {}
    for key in 'source_addr_long', 'serial', 'name':
        value = data.pop(key, None)
        if value is not None:
            tags[key] = value

    # Time
    time = data.pop('tst', None)
    if time is None:
        time = data['received']
    time = datetime.fromtimestamp(time, timezone.utc).isoformat()

    return {'tags': tags, 'frames': [{'time': time, 'data': data}]}


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('paths', nargs='+',
                            help='Path to file or directory')

    def handle(self, *args, **kw):
        # Parse
        frames = []
        for path in kw['paths']:
            assert zipfile.is_zipfile(path)
            self.stdout.write('Parsing %s' % path)
            with zipfile.ZipFile(path, 'r') as zf:
                names = zf.namelist()
                for name in tqdm.tqdm(names):
                    if name.startswith('DATA/') and name.endswith('.TXT'):
                        with zf.open(name) as data_file:
                            for frame in read_wasp_data(data_file):
                                frame = data_to_json(frame)
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
            frames_data = frame.pop('frames')
            metadata, created = Metadata.objects.get_or_create(**frame)
            for frame_data in frames_data:
                time = frame_data['time']
                data = frame_data['data']
                Frame.update_or_create(metadata, time, data)
