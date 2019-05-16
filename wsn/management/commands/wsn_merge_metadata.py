from tqdm import tqdm

# Django
from django.core.management.base import BaseCommand

# WSN
from wsn.models import Frame, Metadata


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--save', action='store_true', default=False)

    def handle(self, *arg, **kw):
        save = kw['save']

        key = 'remote_addr'
        metadatas = Metadata.objects.filter(tags__has_key=key)
        for metadata in metadatas:
            name = metadata.name
            value = metadata.tags[key]
            self.stdout.write(f'id={metadata.id} name="{name}" {key}={value}')
            self.stdout.write(str(metadata.tags))

            # Find the reference metadata (the one that doesn't have the key)
            tags = metadata.tags.copy()
            del tags[key]
            self.stdout.write(str(tags))
            ref = Metadata.objects.filter(name=name, tags=tags)
            n = ref.count()
            if n != 1:
                self.stderr.write(
                    f'expected 1 reference metadatas with "{name}" name, found {n}'
                )
                self.stdout.write('')
                continue
            ref = ref.get()

            # Update frames and delete metadata
            # TODO For performance we should use bulk update, but Django does
            # not yet support bulk update in JSON fields, see
            # https://code.djangoproject.com/ticket/29112
            frames = Frame.objects.filter(metadata=metadata)
            n = frames.count()
            if save:
                for frame in tqdm(frames, total=n):
                    if frame.data is None:
                        frame.data = {}
                    frame.data[key] = value
                    frame.metadata = ref
                    frame.save()

                metadata.delete()
            else:
                self.stdout.write(f'{n} frames would have been updated')

            self.stdout.write('')
