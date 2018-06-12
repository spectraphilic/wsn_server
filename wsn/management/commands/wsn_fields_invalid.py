import datetime
from django.core.management.base import BaseCommand
from wsn.models import Frame


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--delete-old', action='store_true', default=False)
        parser.add_argument('--delete-bad', action='store_true', default=False)

    def log(self, prefix, n, delete):
        suffix = 'frames deleted' if delete else 'frames would be deleted'
        print('{}: {} {}'.format(prefix, n, suffix))

    def handle(self, *args, **kw):
        delete_old = kw['delete_old']
        delete_bad = kw['delete_bad']

        # Old date
        date = datetime.date(2001, 1, 1)
        frames = Frame.objects.filter(time__lt=date)
        if delete_old:
            n, _ = frames.delete()
        else:
            n = frames.count()
        self.log('Invalid time value', n, delete_old)

        # DS1820 bad values (not list)
        n = 0
        for frame in Frame.objects.filter(data__has_key='ds1820'):
            value = frame.data['ds1820']
            if type(value) is not list:
                n += 1
                if delete_bad:
                    frame.delete()
        self.log('Invalid DS1820 value', n, delete_bad)
