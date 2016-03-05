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

development:
	ansible-playbook -i ansible/hosts ansible/active.yml

staging:
	ansible-playbook -i ansible/hosts ansible/active.yml

production:
	ansible-playbook -i ansible/hosts ansible/active.yml

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
