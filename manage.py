#!usr/bin/python
import os
import sys

if __name__ == "__main__":
    if os.path.exists('var/boot'):
        target = open('var/boot').read().strip()
    else:
        target = 'development'

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.%s" % target)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
