# (c) 2013, Jan-Piet Mens <jpmens(at)gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

from ansible import utils, errors
import codecs
from ConfigParser import SafeConfigParser, NoSectionError, NoOptionError

class LookupModule(object):

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def read_ini(self, filename, section, key, dflt=None):

        try:
            f = codecs.open(filename, 'r', encoding='utf-8')
            creader = SafeConfigParser()
            creader.readfp(f)

            return creader.get(section, key)
        except (NoSectionError, NoOptionError):
            pass
        except Exception, e:
            raise errors.AnsibleError("inifile: %s" % str(e))

        return dflt

    def run(self, terms, inject=None, **kwargs):

        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)

        if isinstance(terms, basestring):
            terms = [ terms ]

        ret = []
        for term in terms:
            params = term.split()
            section = params[0]
            key = params[1]

            paramvals = {
                'file' : 'ansible.ini',
                'default' : None,
            }

            # parameters specified?
            try:
                for param in params[2:]:
                    name, value = param.split('=')
                    assert(name in paramvals)
                    paramvals[name] = value
            except (ValueError, AssertionError), e:
                raise errors.AnsibleError(e)

            path = utils.path_dwim(self.basedir, paramvals['file'])

            var = self.read_ini(path, section, key, paramvals['default'])
            if var is not None:
                if type(var) is list:
                    for v in var:
                        ret.append(v)
                else:
                    ret.append(var)
        return ret
