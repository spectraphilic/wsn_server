import textwrap

from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db import transaction

from wsn.models import Frame


class Command(BaseCommand):

    def add_arguments(self, parser):
        default = 15000
        parser.add_argument(
            '--chunk', type=int, default=default,
            help=f'Commit to the database every <chunk> rows, default={default}'
        )
        parser.add_argument(
            'field', nargs='*',
            help='Fields to extract from data (json)'
        )

    def handle(self, *args, **options):
        chunk_size = options['chunk']
        fields = options['field']

        #
        # Verify input
        #
        err = False
        if len(fields) == 0:
            self.stderr.write(f'field missing, pass at least one')
            err = True

        available = set(Frame.get_data_fields())
        for field in fields:
            if field not in available:
                self.stderr.write(f'{field} field not available')
                err = True

        if err:
            self.stdout.write('Pass one or more field from this list:')
            self.stdout.write('\n'.join(
                textwrap.wrap(', '.join(sorted(available, key=lambda x: x.lower())), 80)
            ))
            return

        # Queryset
        frames = Frame.objects.exclude(data=None)
        if len(fields) == 1:
            frames = frames.filter(data__has_key=fields[0])
        else:
            frames = frames.filter(data__has_any_keys=fields)

        # Number of chunks
        n_frames = frames.count()
        n_chunks = n_frames // chunk_size
        if n_frames % chunk_size:
            n_chunks += 1

        # Go
        frames = frames.order_by('id')
        start = 0
        for i in tqdm(range(n_chunks)):
            with transaction.atomic():
                for obj in frames.filter(id__gt=start)[:chunk_size]:
                    obj.extract_from_json(fields, dryrun=False)

                # Next chunk
                start = obj.id
