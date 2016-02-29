#
# Ansible
#

development:
	ln -sfn development.yml ansible/active.yml
	ansible-playbook -i ansible/hosts ansible/active.yml

staging:
	ln -sfn staging.yml ansible/active.yml
	ansible-playbook -i ansible/hosts ansible/active.yml

production:
	ln -sfn production.yml ansible/active.yml
	ansible-playbook -i ansible/hosts ansible/active.yml

update:
ifeq ("$(wildcard ansible/active)","")
	ln -sn development.yml ansible/active.yml
endif
	ansible-playbook -i ansible/hosts ansible/active.yml

# TODO Do with ansible, detect first install
install: update
	./manage.py createsuperuser

#
# Start, stop
#

start:
	uwsgi var/etc/uwsgi.ini

stop:
	uwsgi --stop var/run/uwsgi.pid

reload:
	echo r > var/run/uwsgi.fifo

#
# Help
#

help:
	@echo "Please use 'make <rule>' where <rule> is one of..."
	@echo
	@echo "make install"
	@echo "    Creates the virtual environment, installs the required"
	@echo "    software, and just prepares everything, including"
	@echo "    initilizing the database."
	@echo
	@echo "    This will also set the symbolic link boot/activate, by"
	@echo "    default to the 'development' target. This can be changed"
	@echo "    passing the TARGET option. For instance:"
	@echo
	@echo "    make install BOOT=staging"
	@echo "    make install BOOT=production"
	@echo
	@echo "make update"
	@echo "    Used mainly when deploying in a server. Install the"
	@echo "    required software, etc."
	@echo
