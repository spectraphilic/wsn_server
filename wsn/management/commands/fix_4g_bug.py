"""
This command only works for in-order frames, because it relies on the PK.
This means it doesn't work with:

- Iridium frames
- Old XBee frames
"""

from tabulate import tabulate

from django.core.management.base import BaseCommand
from wsn.models import Frame


NAME = 'sw-002'
#NAME = 'v15@CS'

class Command(BaseCommand):

    def handle(self, *args, **kw):
        frames = Frame.objects.filter(metadata__name=NAME)
        frames = frames.order_by('id')
        #print(f'TOTAL={frames.count()}')

        seq_prev = None
        time_prev = None

        table = []
        for frame in frames:
            pk = frame.pk
            seq = frame.frame
            time = frame.time

            # Sequence number is None only for old RSSI frames in XBee
            # networks, produced at the initiative of the Raspberry Pi.
            if seq is None:
                continue

            # Frame type
            typ = frame.data['type']
            typ = {2: 'Boot', 0: ''}[typ]

            # Sequence distance
            seq_distance = ''
            if typ == 'Boot':
                assert seq == 0
            elif seq_prev is not None:
                if seq_prev <= seq:
                    seq_distance = seq - seq_prev
                else:
                    seq_distance = (255 - seq_prev) + seq

                if seq_distance == 1:
                    seq_distance = ''

            # Time distance
            time_distance = ''
            if time_prev is not None:
                time_distance = (time // 60) - (time_prev // 60)

            table.append((pk, time, typ, seq, seq_distance, time_distance))
            seq_prev = seq
            time_prev = time

        #print()
        headers = ['PK', 'Time', 'Type', 'Sequence', 'Seq distance', 'Time distance']
        print(tabulate(table, headers=headers))
