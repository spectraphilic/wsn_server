# Standard library
from time import time

# Django
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.management.base import BaseCommand
from django.db.models import Func, Value
from django.db import transaction

# WSN
from wsn.models import Frame


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--yes', action='store_true', default=False)
        parser.add_argument('--max', type=int, default=None)

    def handle(self, *arg, **kw):
        t0 = time()
        # The algo to work properly requires the variable received, this means
        # that it only is able to merge frames uploaded via the Raspberry Pi.
        dups = (
            Frame.objects
            .exclude(received=None)
            .values('metadata', 'time')
            .annotate(ids=ArrayAgg('id'))
            .annotate(c=Func('ids', Value(1), function='array_length'))
            .filter(c__gt=1)
        )
        n = dups.count()
        t = time() - t0
        print(f'{n} dups found in {t:.2f} seconds')
        print()

        data_fields = Frame.get_data_fields()
        for i, dup in enumerate(dups):
            if kw['max'] is not None and i >= kw['max']:
                break

            metadata = dup['metadata']
            t = dup['time']
            print(f'{i+1}/{n}: metadata={metadata} time={t}')
            first = None
            # We order by received instead of frame sequence because the frame
            # sequence can wrap (255 + 1 = 0)
            # This relies on frames to be sent in order, which has been true
            # for a long time, before we started splitting frames.
            for frame in Frame.objects.filter(id__in=dup['ids']).order_by('received'):
                assert frame.metadata_id == metadata
                assert frame.time == t
                print(frame.pk, frame.frame, frame.received, frame.data)
                if first is None:
                    first = frame
                    continue

                # Only consecutive frames
                # Ideally we should keep the range or list of frame sequences,
                # but the frame field is an integer, so we can keep only one
                # value, it will be the last one.
                assert (first.frame + 1) % 256 == frame.frame

                # Data fields
                override = {'frame', 'received'}
                for name in data_fields:
                    first_value = getattr(first, name)
                    value = getattr(frame, name)
                    if value is None:
                        pass
                    elif type(first_value) is list and type(value) is list:
                        raise NotImplementedError(f'{name} is a list')
                    elif first_value is None or name in override:
                        setattr(first, name, value)
                        print(f'* {name}={value}')
                    elif first_value != value:
                        assert first_value is None, f'field={name} duped'

                # JSON
                override = {}
                for name in frame.data:
                    first_value = first.data.get(name)
                    value = frame.data.get(name)
                    if value is None:
                        pass
                    elif type(first_value) is list and type(value) is list:
                        first.data[name].extend(value) # The case of DS18B20 and similar
                    elif first_value is None or name in override:
                        first.data[name] = value
                    elif first_value != value:
                        assert first_value is None, f'field=data.{name} duped'

                print(f'* {first.data}')
                if kw['yes']:
                    print("SAVE")
                    with transaction.atomic():
                        frame.delete() # Delete first to avoid integrity error
                        first.save()
                else:
                    print("DON'T SAVE")

            print()
