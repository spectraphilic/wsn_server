import datetime
from django.core.management.base import BaseCommand
from wsn.models import Frame


def get_suffix(delete):
    if delete:
        return 'frames deleted'

    return 'frames would be deleted'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--delete-old', action='store_true', default=False)
        parser.add_argument('--delete-bad', action='store_true', default=False)

    def handle(self, *args, **kw):
        delete_old = kw['delete-old']
        delete_bad = kw['delete-bad']

        # Old date
        date = datetime.date(2001, 1, 1)
        frames = Frame.objects.filter(time__lt=date)
        if delete_old:
            n, _ = frames.delete()
        else:
            n = frames.count()
        suffix = get_suffix(delete_old)
        print('Invalid time value: {} {}'.format(n, suffix))

        # DS1820
        n = 0
        for frame in Frame.objects.filter(data__has_key='ds1820'):
            value = frame.data['ds1820']
            if type(value) is not list:
                n += 1
                if delete_bad:
                    frame.delete()

        suffix = get_suffix(delete_bad)
        print('Invalid DS1820 value: {} {}'.format(n, suffix))
