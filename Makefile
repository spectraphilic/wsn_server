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

dev_conda: dev
	git submodule init
	git submodule update
	ansible-playbook -i ansible/hosts ansible/dev_conda.yml

development:
	git submodule init
	git submodule update
	ansible-playbook -i ansible/hosts ansible/development.yml

production:
	ansible-playbook -i ansible/hosts ansible/production.yml

requirements:
	ansible-playbook -i ansible/hosts ansible/development.yml --tags "pip"

#
# Start, stop
#

start:
	supervisord -c etc/supervisor.conf

stop:
	kill -TERM `cat var/run/supervisord.pid`

ctl:
	supervisorctl -c etc/supervisor.conf

reload:
	kill -HUP `cat var/run/supervisord.pid`
