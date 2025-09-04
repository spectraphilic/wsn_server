
class ClickHouseRouter:

    def db_for_read(self, model, **hints):
        app_label = model._meta.app_label
        if app_label == 'ch':
            return 'clickhouse'

        return None

    def db_for_write(self, model, **hints):
        app_label = model._meta.app_label
        if app_label == 'ch':
            return 'clickhouse'

        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'ch':
            return db == 'clickhouse'

        return False
