import math

from tabulate import tabulate

from django.core.management.base import BaseCommand

from wsn.models import Frame


MAX = 1500000 # Maximum number of rows to analyse
MIN = 100000 # Minimum number of occurrences to print

class Command(BaseCommand):

    def handle(self, *args, **kw):
        #n = Frame.objects.count()
        #print(n)
        types = {}
        freq = {}
        mins = {}
        maxs = {}

        i = 0
        frames = Frame.objects.exclude(data=None)
        for data in frames.values_list('data', flat=True)[:MAX]:
            #print(i)
            i += 1
            for key in data:
                freq[key] = freq.get(key, 0) + 1
                value = data[key]
                new_t = type(value)
                old_t = types.get(key)
                if old_t is None:
                    types[key] = new_t
                elif old_t is int and new_t is float:
                    types[key] = new_t
                elif old_t is float and new_t is int:
                    pass
                elif old_t is float and value == 'NAN':
                    value = math.nan
                elif new_t is not old_t:
                    print('WARNING (%s, %s): %s is not %s' % (key, value, old_t, new_t))
                    continue

                # Min / Max
                if (new_t is int) or (new_t is float and value is not math.nan):
                    old_min = mins.get(key)
                    if old_min is None or value < old_min:
                        mins[key] = value
                    old_max = maxs.get(key)
                    if old_max is None or value > old_max:
                        maxs[key] = value

        #print(i)
        table = []
        for key, f in sorted(freq.items(), key=lambda x: x[1]):
            if f > MIN:
                t = types[key]
                t = {int: 'int', float: 'float'}.get(t, t)
                table.append((key, f, t, mins.get(key), maxs.get(key)))

        print()
        print(tabulate(table, headers=['Name', 'Count', 'Type', 'Min', 'Max']))
