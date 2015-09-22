
TARGET=

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
	@echo "make switch"
	@echo "    Resets the boot/active symbolik link to the given target,"
	@echo "    then installs the required software, etc. Use the TARGET"
	@echo "    option. For example:"
	@echo
	@echo "    make switch BOOT=development"
	@echo "    make switch BOOT=staging"
	@echo "    make switch BOOT=production"
	@echo
	@echo "make update"
	@echo "    Used mainly when deploying in a server. Install the"
	@echo "    required software, etc."
	@echo


#
# Stage 1 (_env) -- Virtual environment
# Stage 2 (_lnk) -- Make the symbolic link to the right target
# Stage 3 (_req) -- Install requirements
# Stage 4 (_bld) -- Build templates, static, ..
# Stage 5 (_syn) -- python manage.py migrate
#
# Install: 1 - 5
# Switch : 2 - 4
# Update : 3 - 4
#

_env:
	virtualenv --setuptools -p /usr/bin/python3 usr
	usr/bin/pip install --upgrade setuptools


_lnk:
ifeq ($(TARGET),)
ifeq ("$(wildcard boot/active)","")
	ln -sn development boot/active
endif
else
ifeq ("$(wildcard boot/$(TARGET))","")
	$(error "boot/$(TARGET)" no such file or directory)
else
	ln -sfn $(TARGET) boot/active
endif
endif


_req:
	usr/bin/pip install -r boot/requirements.txt
ifneq ("$(wildcard boot/active/requirements.txt)","")
	usr/bin/pip install -r boot/active/requirements.txt
endif


_bld:
	./boot/boot.py build
ifneq ("$(wildcard boot/active/Makefile)","")
	$(MAKE) -C boot/active
endif


_syn:
	./manage.py migrate


#
# Rules
#
install: _env _lnk _req _bld _syn
	./manage.py createsuperuser

switch: _lnk _req _bld

update: _req _bld

start:
	uwsgi boot/active/uwsgi.ini

stop:
	uwsgi --stop var/run/uwsgi.pid

reload:
	echo r > var/run/uwsgi.fifo

deploy:
	ansible-playbook -i boot/ansible/hosts boot/ansible/deploy.yml
