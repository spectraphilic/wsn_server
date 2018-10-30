from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db import transaction

from wsn.models import Frame


class Command(BaseCommand):

    def handle(self, *args, **kw):
        # Queryset
        fields = set(Frame.get_data_fields())
        frames = Frame.objects.exclude(data=None).order_by('id')
        start = 0

        # Number of chunks
        chunk_size = 5000
        n_frames = frames.count()
        n_chunks = n_frames // chunk_size
        if n_frames % chunk_size:
            n_chunks += 1

        # Go
        for i in tqdm(range(n_chunks)):
            with transaction.atomic():
                for obj in frames.filter(id__gt=start)[:chunk_size]:
                    obj.extract_from_json(fields)

                # Next chunk
                start = obj.id
