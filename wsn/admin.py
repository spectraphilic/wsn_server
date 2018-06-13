from django.contrib import admin
#from django.urls import reverse
#from django.utils.safestring import mark_safe

from .models import Frame, Metadata

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
    list_display = ['tags']
    readonly_fields = ['tags']
    list_filter = [NameFilter, SerialFilter]


#
# Frames
#
class FrameNameFilter(NameFilter):
    prefix = 'metadata__'

class FrameSerialFilter(SerialFilter):
    prefix = 'metadata__'

class FrameAddressFilter(FrameSerialFilter):
    title = 'address'
    parameter_name = 'source_addr_long'


@admin.register(Frame)
class FrameAdmin(admin.ModelAdmin):
    list_display = ['time_seconds', 'metadata', 'data']
    list_filter = [FrameNameFilter, FrameSerialFilter, FrameAddressFilter]

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = ['time_seconds', 'metadata', 'data']
        fields = [
            name for name in obj.get_data_fields()
            if getattr(obj, name) is not None]

        return readonly_fields + fields

    def time_seconds(self, obj):
        return obj.time.strftime("%Y-%m-%d %H:%M:%S %z")

    time_seconds.admin_order_field = 'time'
    time_seconds.short_description = 'Time'

#   def metadata_link(self, obj):
#       pk = obj.metadata_id
#       href = reverse('admin:wsn_metadata_change', args=[pk])
#       return mark_safe('<a href="{}">{}</a>'.format(href, pk))
