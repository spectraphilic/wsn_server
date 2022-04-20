# Standard Library
from datetime import datetime
from time import time

# Django
from django.db.models import Func, DateField


def attrs(**kw):
    def f(func):
        for k, v in kw.items():
            setattr(func, k, v)
        return func
    return f


def fmt_time(time):
    dt = datetime.utcfromtimestamp(time)
    return dt.strftime("%Y-%m-%d %H:%M:%S %z")


class TimeModelMixin:

    @property
    @attrs(short_description='Time', admin_order_field='time')
    def time_str(self):
        return fmt_time(self.time)


class GetDate(Func):
    """
    Returns the <date> from a unix timestamp. For example:

    frames = Frame.objects.all().annotate(date=GetDate(F('time')))
    frames.values_list('time', 'date')
    frames.distinct('metadata__name', 'date').values('date', 'metadata__name')
    """

    function = 'TO_TIMESTAMP'
    template = '%(function)s(%(expressions)s)::date'
    output_field = DateField()



def import_waspmote_series(series, stdout, merge=True):
    """
    Used by import waspmote commands.
    """
    from wsn.models import frame_to_database

    for serie in series.values():
        tags = serie['tags']
        frames = serie['frames']
        n = len(frames)

        # Sort by time
        #frames.sort(key=lambda x: x['time'])

        # Print
        stdout.write('')
        stdout.write('serial={serial} name={name}'.format(**tags))
        first = frames[0]['time']
        if n > 1:
            last = frames[-1]['time']
            assert first < last
            first = datetime.utcfromtimestamp(first)
            last = datetime.utcfromtimestamp(last)
            stdout.write(f'{n} frames from {first} to {last}')
        else:
            first = datetime.utcfromtimestamp(first)
            stdout.write(f'{n} frame at {first}')

        # Inserting
        yes = input('Insert into database? Yes/[No]: ')
        if yes.lower() == 'yes':
            t0 = time()
            frame_to_database(serie, update=False, merge=merge)
            stdout.write(f'Done in 5{time() - t0} seconds')
