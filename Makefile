help:
	@echo "Please use 'make <rule>' where <rule> is one of..."
	@echo
	@echo "  make local              -- Installs or updates a local development environment"
	@echo "  make local-requirements -- Updates requirements of local development environment"
	@echo "  make install-server     -- Installs or updates server environment"
	@echo "  make deploy-production  -- Remotely updates server environment"
	@echo ""
	@echo "  make start              -- Start the program by runnint Supervisor"
	@echo "  make stop               -- Stop Supervisor"
	@echo "  make reload             -- Reload all programs in Supervisor"
	@echo "  make ctl                -- Run supervisorctl to manage all programs"
	@echo ""

submodules:
	git submodule init
	git submodule update

local: submodules
	ansible-playbook -i ansible/hosts-local ansible/development.yml

local-requirements: submodules
	ansible-playbook -i ansible/hosts-local ansible/development.yml --tags "pip"

install-production: submodules
	ansible-playbook -i ansible/hosts-local ansible/production.yml

deploy-production:
	ansible-playbook -i ansible/hosts-production ansible/production.yml

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
