
help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo
	@echo "  install   -- creates the virtual environment and installs"
	@echo "               the software"
	@echo


install:
	virtualenv --setuptools -p /usr/bin/python2 usr
	usr/bin/pip install --upgrade setuptools
	usr/bin/pip install -r requirements.txt

deploy:
	./boot.py build
	./manage.py collectstatic --noinput

start:
	uwsgi etc/uwsgi.ini

stop:
	uwsgi --stop run/uwsgi.pid

restart:
	uwsgi --stop run/uwsgi.pid
	uwsgi etc/uwsgi.ini
