"""
This file is required for uwsgi to work with Python 2.7, as otherwise importing
ansible.wsgi will fail with the error message:

- ImportError: No module named ansible.wsgi
"""
