import datetime
from django.core.management.base import BaseCommand
from wsn.models import Frame


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', default=False)

    def handle(self, *args, **kw):
        delete = kw['delete']
        if delete:
            suffix = 'frames deleted'
        else:
            suffix = 'frames would be deleted'

        # Old date
        date = datetime.date(2001, 1, 1)
        frames = Frame.objects.filter(time__lt=date)
        if delete:
            n, _ = frames.delete()
        else:
            n = frames.count()
        print('Invalid time value: {} {}'.format(n, suffix))

        # DS1820
        n = 0
        for frame in Frame.objects.filter(data__has_key='ds1820'):
            value = frame.data['ds1820']
            if type(value) is not list:
                n += 1
                if delete:
                    frame.delete()

        print('Invalid DS1820 value: {} {}'.format(n, suffix))
