# FIXME Remove this once psycopg2 2.8 is released
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='psycopg2')


# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
