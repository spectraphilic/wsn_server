#!/usr/bin/env python2

# Import from the Standard Library
from argparse import ArgumentParser
from ConfigParser import ConfigParser
from importlib import import_module
from os import getenv, listdir
from os.path import abspath, dirname, join
from string import Template


def build(parser, args):
    # Load the configuration file
    config = ConfigParser()
    config.read('etc/boot.ini')
    name = config.get('boot', 'name')

    # Get the target
    target = args.target
    try:
        old_target = open('var/boot').read()
    except IOError:
        old_target = None

    if not target:
        target = old_target or 'development' # Default

    if target != old_target:
        open('var/boot', 'w').write(target)

    print 'Build... (target is %s)' % target

    # Load the settings file
    settings = import_module('project.settings.%s' % target)

    # The namespace
    root = abspath(dirname(__file__))
    namespace = {
        'DOMAIN' : ' '.join(settings.ALLOWED_HOSTS),
        'NAME'   : name,
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

        print 'Update', file_out
        template = open(file_in).read()
        template = Template(template)
        data = template.substitute(**namespace)
        open(file_out, 'w').write(data)

    print 'Done.'
    print


if __name__ == '__main__':
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()

    # boot.py build
    parser_build = subparsers.add_parser('build')
    parser_build.add_argument('target', nargs='?')
    parser_build.set_defaults(func=build)

    # Go!
    args = parser.parse_args()
    args.func(parser, args)
