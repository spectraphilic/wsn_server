
# Import from the Standard Library
from ConfigParser import ConfigParser
from os import getenv
from os.path import abspath, dirname
from string import Template
from sys import argv


NAME = 'PROJECT-NAME'
DOMAIN = 'DOMAIN'
GROUP = 'nginx' # www-data for Debian


if __name__ == '__main__':
    # Configuration
    config = {
        'NAME'  : NAME,
        'DOMAIN': DOMAIN,
        'ROOT'  : dirname(abspath(dirname(__file__))),
        'USER'  : getenv('USER'),
        'GROUP' : GROUP,
    }

    # Load uwsgi.ini (unless that is what we are producing)
    cmd, source, target = argv
    if target != 'uwsgi.ini':
        uwsgi = ConfigParser()
        uwsgi.read('uwsgi.ini')
        for key, value in uwsgi.items('uwsgi'):
            config['uwsgi_%s' % key] = value

    # Process file
    template = open(source).read()
    template = Template(template)
    data = template.substitute(**config)
    open(target, 'w').write(data)
