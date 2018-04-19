import math

from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db import transaction

from wsn.models import Frame


class Command(BaseCommand):

    def handle(self, *args, **kw):
        # Queryset
        fields = Frame.get_data_fields()
        frames = Frame.objects.filter(data__has_any_keys=fields)

        # Number of chunks
        chunk_size = 5000
        n_frames = frames.count()
        n_chunks = n_frames // chunk_size
        if n_frames % chunk_size:
            n_chunks += 1

        # Go
        for i in tqdm(range(n_chunks)):
            with transaction.atomic():
                for obj in frames[:chunk_size]:
                    changed = False
                    for key in fields:
                        if key in obj.data:
                            changed = True
                            value = obj.data.pop(key)
                            if value is not None:
                                if value == "NAN":
                                    value = math.nan
                                setattr(obj, key, value)

                    if changed:
                        obj.save()
