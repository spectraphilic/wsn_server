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
	@echo "    Start (or stop, ...) the django instance using asgi."
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

requirements:
	ansible-playbook -i ansible/hosts ansible/development.yml --tags "pip"

#
# Start, stop
#

start:
	gunicorn -c etc/gunicorn.conf.py

stop:
	kill -TERM `cat var/run/asgi.pid`

restart:
	kill -TERM `cat var/run/asgi.pid`
	gunicorn -c etc/gunicorn.conf.py

reload:
	kill -HUP `cat var/run/asgi.pid`


#
# Celery
#

celery:
	celery -A project worker -Q celery_wsn --loglevel=info
