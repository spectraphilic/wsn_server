# Django
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from django.utils.functional import cached_property


# {'source_addr_long': '', 'rf_data': "", 'source_addr': '', 'id': '', 'options': ''}
# {"bat": 93, "serial": 408520806, "received": 1512673261, "humb": 41.20436096191406, "frame": 0, "tcb": 20.849998474121094, "pa": 101.06179809570312, "source_addr_long": 5526146534160749, "tst": 1512680400, "lw": 0.0, "in_temp": 21.25}

class Metadata(models.Model):
    tags = JSONField(default=dict, unique=True, editable=False)

    class Meta:
        indexes = [GinIndex(fields=['tags'])]

    def __str__(self):
        return str(self.tags)


class Frame(models.Model):
    time = models.DateTimeField(null=True, editable=False)
    data = JSONField(editable=False, null=True)
    metadata = models.ForeignKey(Metadata, on_delete=models.CASCADE,
                                 editable=False, related_name='frames',
                                 null=True)

    class Meta:
        ordering = ['-time']
        unique_together = [('time', 'metadata')]

    @cached_property
    def address(self):
        if self.metadata is None:
            return None

        value = self.metadata.tags.get('source_addr_long')
        return ('%016X' % value) if value else None
