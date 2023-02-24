# Django
from django.contrib import admin

from rangefilter.filters import DateRangeFilter

# Project
from . import models
from . import utils


#
# Filters
#

class TimeFilter(DateRangeFilter):

    def _make_query_filter(self, request, validated_data):
        params = super()._make_query_filter(request, validated_data)
        params = {k: v.timestamp() for k, v in params.items()} # To timestamp
        return params


class NameFilter(admin.SimpleListFilter):
    title = 'name'
    parameter_name = 'name'
    prefix = ''
    value_type = str
    value_default = ''

    def pprint(self, value):
        return value

    def lookups(self, request, model_admin):
        name = self.parameter_name
        values = models.Metadata.objects.all().values_list('tags', flat=True)
        values = set(value.get(name, self.value_default) for value in values)
        values = [(value, self.pprint(value)) for value in values]
        values = sorted(values, key=lambda x: x[1])
        return values

    def queryset(self, request, queryset):
        name = self.parameter_name
        value = self.value()
        if value:
            if value == 'null':
                kw = {self.prefix + 'tags__has_key': name}
                return queryset.exclude(**kw)

            value = self.value_type(value)
            kw = {self.prefix + 'tags__contains': {name: value}}
            return queryset.filter(**kw)

        return queryset


class SerialFilter(NameFilter):
    title = 'serial number'
    parameter_name = 'serial'
    value_type = int
    value_default = 0

    def pprint(self, value):
        if value == 0:
            return 'null'

        try:
            return '%016X' % value # integer
        except TypeError:
            return value # string


class FrameSerialFilter(SerialFilter):
    prefix = 'metadata__'


class FrameAddressFilter(FrameSerialFilter):
    title = 'address'
    parameter_name = 'source_addr_long'


#
# Admin
#

def epoch_to_str_plus(time):
    return '-' if time is None else f'{utils.fmt_time(time)} ({time})'


@admin.register(models.Metadata)
class MetadataAdmin(admin.ModelAdmin):
    list_display = ['name', 'tags']
    readonly_fields = ['name', 'tags']
    list_filter = ['name', SerialFilter]
    search_fields = ['name']


@admin.register(models.Frame)
class FrameAdmin(admin.ModelAdmin):
    list_display = ['id', 'time_str', 'frame', 'bat', 'metadata', 'data']
    list_filter = [
        ('time', TimeFilter),
        'metadata__name',
        FrameSerialFilter,
        FrameAddressFilter
    ]

    # Speed up
    show_full_result_count = False

    def get_readonly_fields(self, request, obj=None):
        fields = [
            'metadata',
            'time_str_plus',
            'received_str_plus',
            'inserted_str_plus',
            'frame', 'frame_max',
        ]

        exclude = {'frame', 'received'}
        for name in obj.get_data_fields():
            if name not in exclude and getattr(obj, name) is not None:
                fields.append(name)

        return fields + ['data']

    @utils.attrs(short_description='Time')
    def time_str_plus(self, obj):
        return epoch_to_str_plus(obj.time)

    @utils.attrs(short_description='Received')
    def received_str_plus(self, obj):
        return epoch_to_str_plus(obj.received)

    @utils.attrs(short_description='Inserted')
    def inserted_str_plus(self, obj):
        return epoch_to_str_plus(obj.inserted)

#   def metadata_link(self, obj):
#       pk = obj.metadata_id
#       href = reverse('admin:wsn_metadata_change', args=[pk])
#       return mark_safe('<a href="{}">{}</a>'.format(href, pk))

    def get_form(self, request, obj=None, **kwargs):
        help_texts = {
            'time_str_plus': 'Sampling time',
            'received_str_plus': 'Time the frame was received by the gateway (if any)',
            'inserted_str_plus': 'Time of insert into the database (only available from 2019/11/09)'
        }
        kwargs.update({'help_texts': help_texts})
        return super().get_form(request, obj, **kwargs)
