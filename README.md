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
    $ make dev_venv
    $ source venv/bin/activate

Create a super user the first time. And run the server:

    $ python manage.py createsuperuser
    $ python manage.py runserver

# Deploy

Deployment is as simple as:

    $ make production

## Deploy: Set up a new server environment

Create the database as seen above. Create a user in the server:

    # adduser --disabled-password wsn

TODO
