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
