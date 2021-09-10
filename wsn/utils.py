# Standard Library
import cProfile
import datetime
import os
import pstats
import time

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


def profile(log_file):
    assert os.path.isabs(log_file)

    profiler = cProfile.Profile()
    def decorator(fn):
        def inner(*args, **kwargs):
            # Add a timestamp to the profile output when the callable
            # is actually called.
            base, ext = os.path.splitext(log_file)
            base = base + "-" + time.strftime("%Y%m%dT%H%M%S", time.gmtime())
            final_log_file = base + ext

            result = None
            try:
                result = profiler.runcall(fn, *args, **kwargs)
            finally:
                stats = pstats.Stats(profiler)
                stats.dump_stats(final_log_file)
            return result
        return inner

    return decorator


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
