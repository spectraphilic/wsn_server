# wsn\_server
Software and django applications for wsn and iot setup

# Install

This project only works with PostgreSQL. First create a user and database
(for a local envinronment choose "wsn" as the password):

    $ sudo su - postgres
    postgres@ $ createuser -e -P wsn
    postgres@ $ createdb -e -O wsn wsn

There are 2 options to set up a local environment: Conda and virtualenv.

Conda:

    $ conda create --name wsn
    $ source activate wsn
    $ make dev_conda

Virtual env:

    $ make dev_venv
    $ source venv/bin/activate

Create a super user the first time. And run the server:

    $ python manage.py createsuperuser
    $ python manage.py runserver
