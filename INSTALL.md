To install the project in a server a number of steps are required.

The following instructions assume a Debian or Debian derivative distribution is
used. But the project can be installed in any Linux system, provided the
available software is not too old.

# Requirements

Install the system wide requirements:

    apt install git make postgresql python3-venv rabbitmq-server redis
    apt install certbot monit nginx
    apt install ansible

# Database

This project only works with PostgreSQL. Create a user and database:

    su - postgres
    postgres@ $ createuser -e -P wsn
    postgres@ $ createdb -e -O wsn wsn

If PostgreSQL is configured to allow *peer* connections, then the password
doesn't matter: the `wsn` system user will be able to connect to the database
as the `wsn` PostgreSQL user. This is the default in Debian.

# Create user and clone

Create a user in the server and switch:

    adduser --disabled-password wsn
    su - wsn

Clone the project (as `wsn` user):

    git clone https://github.com/spectraphilic/wsn_server.git
    cd wsn_server

# Python version

The project uses Python 3.9 by default, but will work with 3.8 or later. Verify
which Python version is available:

    $ python3 --version
    Python 3.8.10

And, if it's not 3.9, then just edit the `ansible/vars.yml` file and set the
correct version:

    python_version : "3.8"

# Configuration

There are a number of configuration options in the `ansible/production.yml`
that must be changed for a different deployment.

Set up a domain for the project and then edit the `domains` variable:

    domains:
    - "wsn.example.com"

Change the email address used for Let's Encrypt:

    django_cert:
      email           : "me@example.com"

Start with HTTP only, we will later switch to HTTPS:

    nginx:
      http            : true
      https           : false

# Install

Now we can proceed with the install proper:

    $ make install-production

This may fail if the version of Ansible is too old. If that's the case then do
the following:

    $ python3.9 -m venv venv39
    $ source venv39/bin/activate
    $ pip install ansible
    $ make install-production

Now create a superuser:

    $ source venv39/bin/activate
    $ python manage.py createsuperuser

# Nginx

The configuration file is generated automatically, but we must tell Nginx about
it:

    ln -snf /home/wsn/wsn_server/etc/nginx.conf /etc/nginx/sites-enabled/wsn.conf

Verify the configuration is correct:

    nginx -t

And if it is, then reload the service:

    service nginx reload

# Permissions

For Nginx to have access to the socket file of the Django server, it must have the
permissions to reach it. Otherwise you will get a 502 response and see these errors
in the Nginx logs:

    [...] connect() to unix:/home/wsn/wsn_server/var/run/uvicorn.socket failed (13: Permission denied) [...]

One way to fix this is to set set the executable permission in parent directories,
like this:

    chmod o+x /home/wsn

# Monit

Monit will start the program at boot. And will monitor it by sending a ping
request every minute, restarting the program if it does not answer the request.

The configuration file is generated automatically, but we must tell Monit about
it:

    ln -snf /home/wsn/wsn_server/etc/monit.conf /etc/monit/conf-enabled/wsn.conf

Verify the configuration is correct:

    monit -t

And if it is, then reload the service:

    service monit reload

# HTTPS

Using HTTPS requires some more steps.

Enable HTTPS, edit the `ansible/production.yml` file:

    nginx:
      http            : true
      https           : true

Update the project:

    make install-production

Reload Nginx:

    service nginx reload

Create the certificate:

    ln -snf /home/wsn/wsn_server/etc/certbot.conf /etc/letsencrypt/configs/wsn.conf
    certbot certonly --config /etc/letsencrypt/configs/wsn.conf --agree-tos

Disable HTTP:

    nginx:
      http            : false
      https           : true

At this point you probably need to change permissions of the `/etc/letsencrypt/live`
directory, or the next step will fail with a `Permission denied` error:

    chmod o+x /etc/letsencrypt/live

Update the project:

    make install-production

Reload Nginx:

    service nginx reload

# Update

To update the server to a new version of the project just log in and type
again:

    cd wsn_server
    make install-production

This will automatically reload the program.

In the rare case the Monit or Nginx configuration changes, these services must
be reloaded manually.

It is possible to update the server remotely, for that purpose you will need to
install a local instance. This is explained in the `README.md` file.
