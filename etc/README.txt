
How to deploy on Gentoo.


Once
=======

Uwsgi::

  # echo "www-servers/uwsgi" >> /etc/portage/package.keywords/uwsgi
  # emerge uwsgi
 
Nginx::

  # mkdir /etc/nginx/sites
  # vi /etc/nginx/nginx.conf
  ...
  include /etc/nginx/sites/*.conf;
  ...
  # rc-service nginx restart


Each
=======

Make::

  $ cd <PATH-TO-PROJECT>/etc
  $ make deploy

Nginx::

  # cp <PATH-TO-PROJECT>/etc/nginx.conf /etc/nginx/sites/<PROJECT-NAME>.conf
  # rc-service nginx reload
 
Monit::

  # cp <PATH-TO-PROJECT>/etc/monit.conf /etc/monit.d/<PROJECT-NAME>.conf
  # rc-service monit reload
