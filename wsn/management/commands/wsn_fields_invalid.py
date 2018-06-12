import datetime
from django.core.management.base import BaseCommand
from wsn.models import Frame


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-p', '--pretend', action='store_true', default=False)

    def __log(self, prefix, n, suffix):
        mod = ['would be'] if self.pretend else []
        msg = ' '.join([prefix, str(n), 'frames'] + mod + [suffix])
        self.stdout.write(msg)

    def __delete_old(self):
        date = datetime.date(2001, 1, 1)
        frames = Frame.objects.filter(time__lt=date)
        if self.pretend:
            n = frames.count()
        else:
            n, _ = frames.delete()
        self.__log('Invalid time value:', n, 'deleted')

    def __ds1820_value(self, value):
        if (value is not None) and not (-100 < value < 100):
            return None

        return value

    def __fix_ds1820(self):
        key = 'ds1820'
        n = 0
        for frame in Frame.objects.filter(data__has_key=key):
            value = frame.data[key]
            if type(value) is list:
                new_value = [self.__ds1820_value(x) for x in value]
            else:
                new_value = self.__ds1820_value(value)

            if new_value != value:
                if not self.pretend:
                    frame.data[key] = new_value
                    frame.save()
                n += 1
        self.__log('Invalid DS1820 value:', n, 'fixed')

    def handle(self, *args, **kw):
        self.pretend = kw['pretend']
        self.__delete_old()
        self.__fix_ds1820()
