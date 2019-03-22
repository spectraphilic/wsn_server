#
# Help
#

help:
	@echo "Please use 'make <rule>' where <rule> is one of..."
	@echo
	@echo "make <target-environment>"
	@echo "    Available options: development, staging, production."
	@echo "    Check Makefile, every target is just an Ansible playbook"
	@echo
	@echo "make start / stop / restart / reload"
	@echo "    Start (or stop, ...) the django instance using uwsgi."
	@echo


#
# Ansible
#

dev:
	git submodule init
	git submodule update

dev_conda: dev
	ansible-playbook -i ansible/hosts ansible/dev_conda.yml

dev_venv: dev
	ansible-playbook -i ansible/hosts ansible/dev_venv.yml

production:
	ansible-playbook -i ansible/hosts ansible/production.yml

#
# Start, stop
#

start:
	uwsgi var/etc/uwsgi.ini

stop:
	uwsgi --stop var/run/uwsgi.pid

restart:
	uwsgi --stop var/run/uwsgi.pid
	uwsgi var/etc/uwsgi.ini

reload:
	echo r > var/run/uwsgi.fifo


#
# Celery
#

celery:
	celery -A project worker -Q celery_wsn --loglevel=info
