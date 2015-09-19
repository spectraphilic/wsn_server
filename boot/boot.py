#!/usr/bin/env python3

# Import from the Standard Library
from argparse import ArgumentParser
from configparser import ConfigParser, NoSectionError
from importlib import import_module
from os import getenv, listdir
from os.path import abspath, dirname, exists, join
from string import Template
import sys



class Build(object):

    config = None

    def get_config_value(self, key):
        try:
            return self.config.get('boot', key)
        except NoSectionError:
            return None

    def build(self, parser, args):
        # The configuration file
        config = ConfigParser()
        config.read('boot/active/boot.ini')
        self.config = config

        # Load the settings file
        print('Build...')
        settings = import_module('boot.active.settings')

        # The namespace
        namespace = {
            'DOMAIN' : ' '.join(settings.ALLOWED_HOSTS),
            'NAME'   : self.get_config_value('name'),
            'ROOT'   : root,
            'PIDFILE': join(root, 'var', 'run', 'uwsgi.pid'),
            'SOCKET' : join(root, 'var', 'run', 'uwsgi.socket'),
            'USER'   : getenv('USER'),
            'GROUP'  : 'nginx', # www-data for Debian
        }

        # Process etc
        for filename in listdir('boot/active'):
            if not filename.endswith('.in'):
                continue

            file_in = join('boot/active', filename)
            file_out = file_in[:-3]
            print('Update', file_out)

            # Make a backup of the old file
            if exists(file_out):
                file_bak = file_out + '.bak'
                data = open(file_out).read()
                open(file_bak, 'w').write(data)

            # Update
            template = open(file_in).read()
            template = Template(template)
            data = template.substitute(**namespace)
            open(file_out, 'w').write(data)

        print('Done.')
        print()


if __name__ == '__main__':
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # boot.py build
    parser_build = subparsers.add_parser('build')
    parser_build.set_defaults(func=Build().build)

    # Add the root (..) to sys.path
    root = dirname(dirname(abspath(__file__)))
    sys.path.insert(0, root)

    # Go!
    args = parser.parse_args()
    args.func(parser, args)
