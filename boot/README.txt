How to install a new project in a server
==============================================================

Make::

  $ cd <PATH-TO-PROJECT>
  $ make deploy

Nginx::

  # cp <PATH-TO-PROJECT>/etc/nginx.conf /etc/nginx/sites/<PROJECT-NAME>.conf
  # service nginx reload

Monit::

  # cp <PATH-TO-PROJECT>/etc/monit.conf /etc/monit.d/<PROJECT-NAME>.conf
  # service monit reload


Gentoo
==============================================================

Uwsgi::

  # echo "www-servers/uwsgi python" > /etc/portage/package.use/uwsgi
  # emerge uwsgi

Nginx::

  # mkdir /etc/nginx/sites
  # vi /etc/nginx/nginx.conf
  ...
  include /etc/nginx/sites/*.conf;
  ...
  # service nginx restart
