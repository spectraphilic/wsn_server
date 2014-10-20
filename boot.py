#!/usr/bin/env python2

# Import from the Standard Library
from argparse import ArgumentParser
from ConfigParser import ConfigParser, NoSectionError
from importlib import import_module
from os import getenv, listdir
from os.path import abspath, dirname, exists, join
from string import Template



class Build(object):

    config = None
    target = None

    def get_config_value(self, key):
        config = self.config
        try:
            value = config.get(self.target, 'name')
        except NoSectionError:
            value = None

        return value or config.get('boot', 'name')


    def build(self, parser, args):
        # The configuration file
        config = ConfigParser()
        config.read('etc/boot.ini')
        self.config = config

        # The target
        target = args.target
        try:
            old_target = open('var/boot').read()
        except IOError:
            old_target = None

        if not target:
            target = old_target or 'development' # Default

        if target != old_target:
            open('var/boot', 'w').write(target)

        self.target = target

        # Load the settings file
        print('Build... (target is %s)' % target)
        settings = import_module('project.settings.%s' % target)

        # The namespace
        root = abspath(dirname(__file__))
        namespace = {
            'DOMAIN' : ' '.join(settings.ALLOWED_HOSTS),
            'NAME'   : self.get_config_value('name'),
            'ROOT'   : root,
            'PIDFILE': join(root, 'var', 'run', 'uwsgi.pid'),
            'SOCKET' : join(root, 'var', 'run', 'uwsgi.socket'),
            'USER'   : getenv('USER'),
            'GROUP'  : 'nginx', # www-data for Debian
            'TARGET' : target,
        }

        # Process etc
        for filename in listdir('etc'):
            if not filename.endswith('.in'):
                continue

            file_in = join('etc', filename)
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
    parser_build.add_argument('target', nargs='?')
    parser_build.set_defaults(func=Build().build)

    # Go!
    args = parser.parse_args()
    args.func(parser, args)
