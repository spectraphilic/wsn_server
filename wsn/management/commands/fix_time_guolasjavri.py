from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.models import F
from wsn.models import Frame


NAME = 'pf-guolasjavri'
T0 = int(datetime(2019, 12, 1).timestamp())
T1 = int(datetime(2020, 7, 1).timestamp())
GAP = 6563278 # seconds


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--save', action='store_true', default=False)

    def handle(self, *arg, **kw):
        save = kw['save']

        frames = Frame.objects.filter(metadata__name=NAME, time__gte=T0, time__lte=T1)
        print(frames.count())

        if save:
            n = frames.update(time=F('time') + GAP)
            print(n, frames.count())
