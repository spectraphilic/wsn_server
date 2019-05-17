# Django
from django.core.management.base import BaseCommand
from django.db import IntegrityError

# WSN
from wsn.models import Frame, Metadata


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--save', action='store_true', default=False)
        parser.add_argument('--limit', type=int, default=None)
        parser.add_argument('--quiet', action='store_true', default=False)

    def handle(self, *arg, **kw):
        save = kw['save']
        limit = kw['limit']
        quiet = kw['quiet']

        key = 'remote_addr'
        metadatas = Metadata.objects.filter(tags__has_key=key)
        i = 0
        for metadata in metadatas:
            name = metadata.name
            value = metadata.tags[key]

            # Find the reference metadata (the one that doesn't have the key)
            tags = metadata.tags.copy()
            del tags[key]
            ref = Metadata.objects.filter(name=name, tags=tags)
            n = ref.count()
            if n != 1:
                if not quiet:
                    self.stdout.write(
                        f'metadata id={metadata.id} name="{name}" tags={metadata.tags}'
                    )
                    self.stdout.write(
                        f'WARNING found {n} metadatas with name={name} tags={tags}'
                    )
                    self.stdout.write('')
                continue

            # Limit
            i += 1
            if limit and i > limit:
                break

            ref = ref.get()
            self.stdout.write(
                f'metadata id={metadata.id} name="{name}" tags={metadata.tags}'
            )
            self.stdout.write(
                f'metadata(ref) id={ref.id} name="{ref.name}" tags={ref.tags}'
            )

            # Update frames and delete metadata
            # TODO For performance we should use bulk update, but Django does
            # not yet support bulk update in JSON fields, see
            # https://code.djangoproject.com/ticket/29112
            frames = Frame.objects.filter(metadata=metadata)
            for frame in frames:
                self.stdout.write(
                    f'frame id={frame.id} metadata={metadata.id} time={frame.time} data={frame.data}'
                )
                if frame.data is None:
                    frame.data = {}
                frame.data[key] = value
                frame.metadata = ref
                if save:
                    try:
                        frame.save()
                    except IntegrityError:
                        dup = Frame.objects.get(metadata=ref, time=frame.time, frame=frame.frame)
                        self.stdout.write(f'WARNING frame id={frame.id} dup={dup.id}')
                        break

                    self.stdout.write(
                        f'frame id={frame.id} metadata={metadata.id} time={frame.time} data={frame.data} SAVED'
                    )
                else:
                    self.stdout.write(
                        f'frame id={frame.id} metadata={metadata.id} time={frame.time} data={frame.data} *NOT* saved'
                    )
            else:
                if save:
                    metadata.delete()

            self.stdout.write('')
