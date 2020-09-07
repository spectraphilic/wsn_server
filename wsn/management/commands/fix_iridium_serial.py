"""
Rename serial to device_serial.
"""

from django.core.management.base import BaseCommand
from wsn.models import Frame, Metadata


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--save', action='store_true', default=False)

    def handle(self, *arg, **kw):
        save = kw['save']

        metadatas = Metadata.objects.filter(tags__device_type='ROCKBLOCK')
        for metadata in metadatas:
            tags = metadata.tags
            print(metadata)
            if 'device_serial' not in tags:
                if save:
                    tags['device_serial'] = tags.pop('serial')
                    metadata.tags = tags
                    metadata.save()
                    print(f'{metadata}')
                    print()

