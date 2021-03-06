"""
This command only works for in-order frames, because it relies on the PK.
This means it doesn't work with:

- Iridium frames
- Old XBee frames
"""

from datetime import datetime
from tabulate import tabulate

from django.core.management.base import BaseCommand
from wsn.models import Frame


NAME = 'sw-002'
#NAME = 'v15@CS'

class Command(BaseCommand):

    def handle(self, *args, **kw):
        frames = Frame.objects.filter(metadata__name=NAME)
        frames = frames.order_by('id')

        seq_prev = None
        time_prev = None

        table = []
        for frame in frames:
            pk = frame.pk
            seq = frame.frame
            seq_max = frame.frame_max
            time = frame.time

            if seq_max is None:
                seq_max = seq

            # Sequence number is None only for old RSSI frames in XBee
            # networks, produced at the initiative of the Raspberry Pi.
            if seq is None:
                continue

            # Frame type
            typ = frame.data['type']
            typ = {2: 'Boot', 0: ''}[typ]

            # Frame sequence
            if seq_max == seq:
                seq_txt = seq
            else:
                seq_txt = f'{seq}-{seq_max}'

            # Sequence distance
            seq_distance = ''
            if typ == 'Boot':
                assert seq == 0
            elif seq_prev is not None:
                if seq_prev <= seq:
                    seq_distance = seq - seq_prev
                else:
                    seq_distance = (256 - seq_prev) + seq

                if seq_distance == 1:
                    seq_distance = ''

            # Time
            time_txt = datetime.utcfromtimestamp(time).strftime('%Y-%m-%d %H:%M:%S')
            time_distance = ''
            if time_prev is not None:
                time_distance = (time // 60) - (time_prev // 60)

            table.append((pk, time_txt, typ, seq_txt, seq_distance, time_distance))

            # Next
            seq_prev = seq_max
            time_prev = time

        headers = ['PK', 'Time', 'Type', 'Sequence', 'Seq distance', 'Time distance']
        print(tabulate(table, headers=headers))
