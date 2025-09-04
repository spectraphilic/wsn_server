from django.apps import AppConfig


class ChConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ch'
    verbose_name = 'ClickHouse'
