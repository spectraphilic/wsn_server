django-boot adds support for different environments (developement, staging,
production, ...) to Django:

- Start a new project by cloning
- Update with new features by pulling
- Add django-boot to your existing project
- Deploy in a server, integrates with: uwsgi, nginx, monit


How to start a new project
=============================================

::

  $ git clone https://github.com/jdavid/django-boot.git myproject
  $ cd myproject
  $ git remote rename origin boot
  $ git remote add origin <my-url>
  $ git push -u origin master

At the end there will be two remotes. The project's origin. And the boot
remote, useful to get future improvements of django-boot.


How to update to a new django-boot
=============================================

::

  $ git pull boot master


How to add django-boot to an existing project
=============================================

::

  $ git remote add boot https://github.com/jdavid/django-boot.git

TODO


Usage: Intall
=============================================

::

  $ make install


uwsgi
=============================================


How to install a new project in a server
==============================================================

Make::

  $ cd <PATH-TO-PROJECT>
  $ make install TARGET=staging

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
