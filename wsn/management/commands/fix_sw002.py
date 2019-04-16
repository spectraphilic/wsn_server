"""
This command only works for in-order frames, because it relies on the PK.
This means it doesn't work with:

- Iridium frames
- Old XBee frames
"""

from django.core.management.base import BaseCommand
from wsn.models import Frame
from wsn.api_4g import postfix


NAME = 'sw-002'
#NAME = 'v15@CS'

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--save', action='store_true', default=False)

    def handle(self, *args, **kw):
        save = kw['save']
        if save is False:
            print("Pass the --save option to save the changes.")

        frames = Frame.objects.filter(metadata__name=NAME).order_by('id')
        for frame in frames:
            postfix(frame, save=save, verbose=True)
