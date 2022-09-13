[![Build Status](https://travis-ci.org/spectraphilic/wsn_server.svg?branch=master)](http://travis-ci.org/spectraphilic/wsn_server)

# wsn\_server
Software and django applications for wsn and iot setup

# Database

This project only works with PostgreSQL. First create a user and database
(for a local envinronment choose "wsn" as the password):

    $ sudo su - postgres
    postgres@ $ createuser -e -P wsn
    postgres@ $ createdb -e -O wsn wsn

# Install

There are 2 options to set up a local environment: Conda and virtualenv.
Choose the one you are most comfortable with.

The build system uses Ansible. If using Conda install it within the Conda
environment. If using virtual environment, then install Ansible system wide.

Conda:

    $ conda create --name wsn
    $ source activate wsn
    $ pip install ansible
    $ make dev_conda

Virtual env:

    $ sudo apt-get install python3-venv # Required in Debian derivatives
    $ sudo apt-get install ansible
    $ make development
    $ source venv/bin/activate

Create a super user the first time. And run the server:

    $ python manage.py createsuperuser
    $ python manage.py runserver

# Deploy

Deployment is as simple as:

    $ make production

## Deploy: Set up a new server environment

System wide requirements:

    $ sudo apt-get install python3-venv # Required in Debian derivatives
    $ sudo apt-get install nginx monit rabbitmq-server

Create the database as seen above. If PostgreSQL is configured to allow *peer*
connections, then the password doesn't matter: the wsn system user will be able
to connect to the database as the wsn PostgreSQL user. This is the default in
Debian.

Create a user in the server:

    # adduser --disabled-password wsn

TODO Server parameters.

Deploy for the first time, fromt the local machine:

    $ make production

Nginx and monit:

    # ln -snf /home/wsn/wsn_server/etc/nginx.conf /etc/nginx/sites-enabled/wsn.conf
    # nginx -t
    # service nginx reload

    # ln -snf /home/wsn/wsn_server/etc/monit.conf /etc/monit/conf-enabled/wsn.conf
    # monit -t
    # service monit reload

Switching to HTTPS requires some more steps:

    $ vi [...]
    $ make production

    # service nginx reload
    # ln -snf /home/wsn/wsn_server/etc/certbot.conf /etc/letsencrypt/configs/wsn.conf
    # certbot certonly --config /etc/letsencrypt/configs/wsn.conf --agree-tos --dry-run
    # certbot certonly --config /etc/letsencrypt/configs/wsn.conf --agree-tos

    $ vi [...]
    $ make production

    # service nginx reload
