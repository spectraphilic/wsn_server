from django.contrib.admin import apps


class MyadminConfig(apps.AdminConfig):
    default_site = 'myadmin.admin.MyadminSite'
