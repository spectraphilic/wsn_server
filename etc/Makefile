
all: uwsgi.ini monit.conf nginx.conf

uwsgi.ini: uwsgi.ini.in etc.py
	python2 etc.py $< $@

monit.conf: monit.conf.in etc.py uwsgi.ini
	python2 etc.py $< $@

nginx.conf: nginx.conf.in etc.py uwsgi.ini
	python2 etc.py $< $@
