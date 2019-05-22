import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings_ansible')

app = Celery('wsn')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.ONCE = {
    'backend': 'celery_once.backends.File',
    'settings': {
        #'location': '/tmp/celery_once',
        #'default_timeout': 60 * 60
    }
}

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
