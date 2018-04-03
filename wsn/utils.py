from cProfile import Profile
import os
import pstats
import time


def profile(log_file):
    assert os.path.isabs(log_file)

    profiler = Profile()
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
