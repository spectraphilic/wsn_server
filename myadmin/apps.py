from django.contrib.admin.apps import AdminConfig


class MyadminConfig(AdminConfig):
    default_site = 'myadmin.admin.MyadminSite'
