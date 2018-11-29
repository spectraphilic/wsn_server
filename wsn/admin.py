import datetime

from django.contrib import admin
#from django.urls import reverse
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


#
# Frames
#
class FrameSerialFilter(SerialFilter):
    prefix = 'metadata__'

class FrameAddressFilter(FrameSerialFilter):
    title = 'address'
    parameter_name = 'source_addr_long'

@admin.register(Frame)
class FrameAdmin(admin.ModelAdmin):
    list_display = ['time_str', 'metadata', 'data']
    list_filter = ['metadata__name', FrameSerialFilter, FrameAddressFilter]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ['time_str_plus', 'metadata', 'data']
        fields = [
            name for name in obj.get_data_fields()
            if getattr(obj, name) is not None]

        return readonly_fields + fields

    @attrs(short_description='Time', admin_order_field='time')
    def time_str(self, obj):
        dt = datetime.datetime.utcfromtimestamp(obj.time)
        return dt.strftime("%Y-%m-%d %H:%M:%S %z")

    @attrs(short_description='Time')
    def time_str_plus(self, obj):
        dt = datetime.datetime.utcfromtimestamp(obj.time)
        dt = dt.strftime("%Y-%m-%d %H:%M:%S %z")
        return f'{dt} ({obj.time})'


#   def metadata_link(self, obj):
#       pk = obj.metadata_id
#       href = reverse('admin:wsn_metadata_change', args=[pk])
#       return mark_safe('<a href="{}">{}</a>'.format(href, pk))
