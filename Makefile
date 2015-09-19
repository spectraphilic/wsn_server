
TARGET=

help:
	@echo "Please use 'make <rule>' where <rule> is one of..."
	@echo
	@echo "make target"
	@echo "    Creates the symlink to the target environement, by default"
	@echo "    'development'."
	@echo
	@echo "    To use another target pass the TARGET option, for example:"
	@echo "    'make target TARGET=staging'"
	@echo
	@echo "    You may pass the TARGET option to these rules: install."
	@echo
	@echo "make install"
	@echo "    Creates the virtual environment and installs the software."
	@echo

#
# target
#
target:
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


# setup
setup: target
	virtualenv --setuptools -p /usr/bin/python3 usr
	usr/bin/pip install --upgrade setuptools

# requirements
requirements:
	usr/bin/pip install -r boot/requirements.txt
ifneq ("$(wildcard boot/$(TARGET))","")
	usr/bin/pip install -r boot/active/requirements.txt
endif

# install
install: setup requirements


#
# more...
#
update: requirements
	./boot/boot.py build
	./manage.py collectstatic --noinput

start:
	uwsgi boot/active/uwsgi.ini

stop:
	uwsgi --stop var/run/uwsgi.pid

restart: stop start
