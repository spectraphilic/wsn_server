import datetime

from django.contrib import admin
from rangefilter.filters import DateTimeRangeFilter

from . import models
from . import models_unmanaged


def get_fields(model, replace=None):
    if replace is None:
        replace = {}

    return [replace.get(field.name, field.name) for field in model._meta.get_fields()]


class ReadOnlyModelAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


def make_readonly_admin_with_formatted_timestamp(model_class, timestamp_field='timestamp'):
    class DynamicTimestampAdmin(ReadOnlyModelAdmin):
        def __init__(self, model, admin_site):
            replace = {timestamp_field: 'formatted_timestamp'}
            self.list_display = get_fields(model, replace=replace)
            super().__init__(model, admin_site)

        @admin.display(description=timestamp_field.capitalize(), ordering=timestamp_field)
        def formatted_timestamp(self, obj):
            ts_value = getattr(obj, timestamp_field)
            if ts_value is None:
                return None
            # Optional: handle milliseconds (remove if all timestamps are in seconds)
            if ts_value > 1e10:
                ts_value /= 1000
            dt = datetime.datetime.fromtimestamp(ts_value, tz=datetime.timezone.utc)
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    DynamicTimestampAdmin.__name__ = f'{model_class.__name__}Admin'
    return DynamicTimestampAdmin


models_to_register = [
    models_unmanaged.FinseSommer,
    models_unmanaged.FinsefluxBiomet,
    models_unmanaged.FinsefluxStationstatus,
    models_unmanaged.GruvebadetData,
    models_unmanaged.GruvebadetDiagnostic,
    models_unmanaged.Mammamia3Mm3Borehole,
    models_unmanaged.Mammamia3Mm3Surface,
    models_unmanaged.Mobileflux2Biomet,
    models_unmanaged.MobilefluxBiomet,
    models_unmanaged.MobilefluxStationstatus,
]

for model in models_to_register:
    admin.site.register(model, make_readonly_admin_with_formatted_timestamp(model))


@admin.register(models_unmanaged.FinsefluxHfdata)
class FinsefluxHfdataAdmin(ReadOnlyModelAdmin):
    list_display = get_fields(models_unmanaged.FinsefluxHfdata, replace={'timestamp': 'formatted_timestamp'})
    list_filter = [
        ('timestamp', DateTimeRangeFilter),
    ]

    @admin.display(description='Timestamp', ordering='timestamp')
    def formatted_timestamp(self, obj):
        # Format the timestamp with milliseconds
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


@admin.register(models_unmanaged.MobilefluxHfdata)
class MobilefluxHfdataAdmin(ReadOnlyModelAdmin):
    list_display = get_fields(models_unmanaged.MobilefluxHfdata, replace={'timestamp': 'formatted_timestamp'})
    list_filter = [
        ('timestamp', DateTimeRangeFilter),
    ]

    @admin.display(description='Timestamp', ordering='timestamp')
    def formatted_timestamp(self, obj):
        # Format the timestamp with milliseconds
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


@admin.register(models.FinsefluxPostproc)
class FinsefluxPostproc(ReadOnlyModelAdmin):
    list_display = get_fields(models.FinsefluxPostproc)
