# Django
from django.core.management.base import BaseCommand

# WSN
from wsn.models import Frame, Metadata


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--save', action='store_true', default=False)
        parser.add_argument('--limit', type=int, default=None)

    def handle(self, *arg, **kw):
        save = kw['save']
        limit = kw['limit']

        key = 'remote_addr'
        metadatas = Metadata.objects.filter(tags__has_key=key)
        if limit:
            metadatas = metadatas[:limit]
        for metadata in metadatas:
            name = metadata.name
            value = metadata.tags[key]
            self.stdout.write(
                f'metadata id={metadata.id} name="{name}" tags={metadata.tags}'
            )

            # Find the reference metadata (the one that doesn't have the key)
            tags = metadata.tags.copy()
            del tags[key]
            ref = Metadata.objects.filter(name=name, tags=tags)
            n = ref.count()
            if n != 1:
                self.stdout.write(
                    f'WARNING found {n} metadatas with name={name} tags={tags}'
                )
                self.stdout.write('')
                continue

            ref = ref.get()
            self.stdout.write(
                f'metadata(ref) id={ref.id} name="{ref.name}" tags={ref.tags}'
            )

            # Update frames and delete metadata
            # TODO For performance we should use bulk update, but Django does
            # not yet support bulk update in JSON fields, see
            # https://code.djangoproject.com/ticket/29112
            frames = Frame.objects.filter(metadata=metadata)
            n = frames.count()
            if save:
                for frame in frames:
                    self.stdout.write(
                        f'frame id={frame.id} metadata={metadata.id} time={frame.time} data={frame.data}'
                    )
                    if frame.data is None:
                        frame.data = {}
                    frame.data[key] = value
                    frame.metadata = ref
                    frame.save()
                    self.stdout.write(
                        f'frame id={frame.id} metadata={metadata.id} time={frame.time} data={frame.data} SAVED'
                    )
                else:
                    metadata.delete()
            else:
                self.stdout.write(f'{n} frames would have been updated')

            self.stdout.write('')
