from django.contrib import admin

from . import models


@admin.register(models.Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(models.Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ['site', 'name', 'lat', 'lng']
    list_filter = [
        'site__name',
    ]


@admin.register(models.Data)
class DataAdmin(admin.ModelAdmin):
    list_display = [
        'node', 'time_str',
        'temperature', 'temperature_qc',
        'humidity', 'humidity_qc',
        'air_pressure', 'air_pressure_qc',
        'snow_depth', 'snow_depth_qc',
    ]
    list_filter = ['node__site__name', 'node__name']

    fields = list_display
    readonly_fields = fields
