import os

from project.settings import *  # noqa: F403


CELERY_TASK_MAX_RETRIES = 0
CLICKHOUSE_NAME = 'test_wsn'
WSN_DATA_DIR = '/tmp'

# GitHub Actions uses service containers, which require TCP connections
if os.environ.get('CI'):
    DATABASES['default']['HOST'] = 'localhost'
    DATABASES['default']['PORT'] = '5432'
    DATABASES['clickhouse']['HOST'] = 'localhost'
