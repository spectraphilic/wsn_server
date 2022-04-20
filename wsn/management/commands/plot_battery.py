# Standard library
from datetime import datetime
import sys

# Requirements
import matplotlib.pyplot as plt
import pandas as pd

# Django
from django.core.management.base import BaseCommand

# Project
from wsn.models import Frame


ts2dt = lambda x: datetime.utcfromtimestamp(x)


def info(name):
    frames = Frame.objects.filter(metadata__name=name)
    frames = frames.filter(time__gt=datetime(2001, 1, 1).timestamp())
    frames = frames.order_by('time').values_list('time', 'bat')
    frames = ((datetime.utcfromtimestamp(time), bat) for time, bat in frames)
    df = pd.DataFrame(frames, columns=['time', 'bat'])
    print(df.head())
    ax = df.plot(x='time', y='bat', linestyle='', marker='.')
    ax.set_title(name)
    plt.show()


class Command(BaseCommand):

    def add_arguments(self, parser):
        add_argument = parser.add_argument
        add_argument('name', help='Name of the node to plot')

    def handle(self, name, *args, **kw):
        info(name)
