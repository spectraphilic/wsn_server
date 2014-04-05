How to install required system-wide software in Gentoo
==============================================================

Uwsgi::

  # echo "www-servers/uwsgi" > /etc/portage/package.keywords/uwsgi
  # emerge uwsgi
 
Nginx::

  # mkdir /etc/nginx/sites
  # vi /etc/nginx/nginx.conf
  ...
  include /etc/nginx/sites/*.conf;
  ...
  # service nginx restart
