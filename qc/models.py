from django.db import models
from wsn.utils import TimeModelMixin


class Site(models.Model):

    name = models.CharField(max_length=80)

    def __str__(self):
        return self.name


class Node(models.Model):

    name = models.CharField(max_length=80, unique=True)
    site = models.ForeignKey(Site, models.PROTECT, null=True)
    lat = models.FloatField('Latitude', null=True, blank=True)
    lng = models.FloatField('Longitude', null=True, blank=True)

    def __str__(self):
        site = self.site
        if site is not None:
            return f'{self.name} ({site.name})'

        return self.name


class Data(TimeModelMixin, models.Model):

    class Meta:
        unique_together = [('node', 'time')]
        verbose_name = 'Data'
        verbose_name_plural = 'Data'

    node = models.ForeignKey(Node, models.PROTECT, editable=False, related_name='data')
    time = models.IntegerField(null=True, editable=False)

    # Data
    temperature = models.FloatField(editable=False)
    temperature_qc = models.BooleanField(editable=False)
    humidity = models.FloatField(editable=False)
    humidity_qc = models.BooleanField(editable=False)
    air_pressure = models.FloatField(editable=False)
    air_pressure_qc = models.BooleanField(editable=False)
    snow_depth = models.FloatField(editable=False)
    snow_depth_qc = models.BooleanField(editable=False)

    def __str__(self):
        return f'{self.node.name} {self.time_str}'
