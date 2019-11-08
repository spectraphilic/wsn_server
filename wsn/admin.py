import datetime

from django.contrib import admin
from django.core.paginator import Paginator
from django.db import connection, transaction
#from django.urls import reverse
from django.utils.functional import cached_property
#from django.utils.safestring import mark_safe

from .models import Frame, Metadata


#
# Utilities
#
def attrs(**kw):
    def f(func):
        for k, v in kw.items():
            setattr(func, k, v)
        return func
    return f


class EstimatedCountPaginator(Paginator):
    """
    From https://code.djangoproject.com/ticket/8408#comment:49
    See also https://hakibenita.com/optimizing-the-django-admin-paginator
    And https://www.citusdata.com/blog/2016/10/12/count-performance/
    """

    @cached_property
    def count(self):
        # The filtered search is not optimazed
        # TODO Usign a function that parses EXPLAIN, see links
        if self.object_list.query.where:
            return self.object_list.count()

        # Speed up the unfiltered search (total count)
        db_table = self.object_list.model._meta.db_table
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
            f"""
                SELECT
                  (reltuples/relpages) * (
                    pg_relation_size('{db_table}') /
                    (current_setting('block_size')::integer)
                  )
                  FROM pg_class where relname = '{db_table}'
            """)
            result = cursor.fetchone()
            if not result:
                return 0
            return int(result[0])

#
# Metadata
#

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
        values = Metadata.objects.all().values_list('tags', flat=True)
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

        return '%016X' % value


@admin.register(Metadata)
class MetadataAdmin(admin.ModelAdmin):
    list_display = ['name', 'tags']
    readonly_fields = ['name', 'tags']
    list_filter = ['name', SerialFilter]
    search_fields = ['name']


#
# Frames
#
class FrameSerialFilter(SerialFilter):
    prefix = 'metadata__'

class FrameAddressFilter(FrameSerialFilter):
    title = 'address'
    parameter_name = 'source_addr_long'


def epoch_to_str_plus(time):
    if time is None:
        return '-'

    dt = datetime.datetime.utcfromtimestamp(time)
    dt = dt.strftime("%Y-%m-%d %H:%M:%S %z")
    return f'{dt} ({time})'


@admin.register(Frame)
class FrameAdmin(admin.ModelAdmin):
    list_display = ['time_str', 'frame', 'metadata', 'data']
    list_filter = ['metadata__name', FrameSerialFilter, FrameAddressFilter]
    show_full_result_count = False
    paginator = EstimatedCountPaginator

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

    @attrs(short_description='Time', admin_order_field='time')
    def time_str(self, obj):
        dt = datetime.datetime.utcfromtimestamp(obj.time)
        return dt.strftime("%Y-%m-%d %H:%M:%S %z")

    @attrs(short_description='Time')
    def time_str_plus(self, obj):
        return epoch_to_str_plus(obj.time)

    @attrs(short_description='Received')
    def received_str_plus(self, obj):
        return epoch_to_str_plus(obj.received)

    @attrs(short_description='Inserted')
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
