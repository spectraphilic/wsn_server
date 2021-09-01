from django.contrib import admin
from qc import models


@admin.register(models.Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(models.Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ['site', 'name']
    list_filter = ['site__name']


@admin.register(models.Data)
class DataAdmin(admin.ModelAdmin):
    list_display = ['node', 'time', 'temperature', 'temperature_qc']
    list_filter = ['node__site__name', 'node__name']
