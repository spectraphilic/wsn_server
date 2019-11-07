from tqdm import tqdm

from django.core.management.base import BaseCommand

from wsn.models import Frame


class Command(BaseCommand):

    def handle(self, *args, **kw):
        used = []
        unused = []
        for name in tqdm(Frame.get_data_fields()):
            n = Frame.objects.exclude(**{name: None}).count()
            if n > 0:
                used.append((name, n))
            else:
                unused.append(name)

        print()
        print('Used:')
        for name, n in used:
            print(name, n)

        print()
        print('Unused:')
        for name in unused:
            print(name)
