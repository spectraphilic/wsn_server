# Standard Library
import datetime

# Django
from django.db.models import Func, DateField


def attrs(**kw):
    def f(func):
        for k, v in kw.items():
            setattr(func, k, v)
        return func
    return f


def fmt_time(time):
    dt = datetime.datetime.utcfromtimestamp(time)
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
