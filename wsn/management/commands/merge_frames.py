# Standard library
from time import time

# Django
from django.core.management.base import BaseCommand
from django.db.models import Count

# WSN
from wsn.models import Frame


def print_frame_line(frame):
    if frame.frame_max is not None:
        print(f'> {frame.pk} {frame.frame}-{frame.frame_max} {frame.received} {frame.data}')
    else:
        print(f'> {frame.pk} {frame.frame} {frame.received} {frame.data}')


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', default=False)
        parser.add_argument('--max', type=int, default=None)

    def handle(self, *arg, **kw):
        t0 = time()

        # We only merge frames coming from the motes, because they're the only
        # we split.
        frames = Frame.objects.exclude(frame=None)

        # The algo to work properly requires the variable received, this means
        # that it only is able to merge frames uploaded via the Raspberry Pi.
        #
        # XXX In practice only frames configured to use the Xbee are split. But
        # if they're uploaded directly from the SD they won't have the received
        # field, so this code won't work in that case.
        frames = frames.exclude(received=None)

        dups = (
            frames
            .values('metadata', 'time')
            .annotate(c=Count('id'))
            .filter(c__gt=1)
            .values('metadata', 'time')
        )
        n = dups.count()
        t = time() - t0
        print(f'{n} dups found in {t:.2f} seconds')
        print()

        for i, dup in enumerate(dups):
            if kw['max'] is not None and i >= kw['max']:
                break

            metadata = dup['metadata']
            t = dup['time']
            print(f'{i+1}/{n}: metadata={metadata} time={t}')
            first = Frame.merge_frames(metadata, t, save=kw['yes'], debug=print_frame_line)
            print_frame_line(first)
            print()
