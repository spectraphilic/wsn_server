from django.contrib import admin

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


@admin.register(models_unmanaged.FinsefluxHfdata)
class FinsefluxHfdataAdmin(ReadOnlyModelAdmin):
    list_display = get_fields(models_unmanaged.FinsefluxHfdata, replace={'timestamp': 'formatted_timestamp'})

    @admin.display(description='Timestamp', ordering='timestamp')
    def formatted_timestamp(self, obj):
        # Format the timestamp with milliseconds
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


@admin.register(models.FinsefluxPostproc)
class FinsefluxPostproc(ReadOnlyModelAdmin):
    list_display = get_fields(models.FinsefluxPostproc)
