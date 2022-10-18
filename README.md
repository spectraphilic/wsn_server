[![Build Status](https://travis-ci.org/spectraphilic/wsn_server.svg?branch=master)](http://travis-ci.org/spectraphilic/wsn_server)

# wsn\_server

Software and django applications for wsn and iot setup.

For instructions on how to install the project in a server, see the
`INSTALL.md` file.

# Local install for development

Install the system wide requirements:

    apt install git make postgresql python3-venv rabbitmq-server
    apt install ansible

Create the PostgreSQL database:

    su - postgres
    postgres@ $ createuser -e -P wsn
    postgres@ $ createdb -e -O wsn wsn

Clone the project and install:

    git clone https://github.com/spectraphilic/wsn_server.git
    cd wsn_server
    make local

Create a superuser, and run the server:

    source venv39/bin/activate
    python manage.py createsuperuser
    make start

# Update a server deployment

If you have deployed the project in a server, see `INSTALL.md`, then you can
update it remotely from your local instance.

Edit the `ansible/hosts-production` file, you will need to specify the hostname
or ip address of the server, the user to log with, and the absolute path where
the project is deployed. For example:

    [hosts]
    wsn.example.com ansible_ssh_user=wsn django_root=/home/wsn/wsn_server

For the deployment to work add your public ssh key to the list of authorized
keys in the server, so this should just work:

    ssh wsn@wsn.example.com

Then to update the server just type:

    make deploy-production

This will automatically reload the program. But won't reload Nginx/Monit.
