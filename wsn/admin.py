from django.contrib import admin
from .models import Frame, Metadata

#
# Metadata
#

@admin.register(Metadata)
class MetadataAdmin(admin.ModelAdmin):
    list_display = ['tags']
    readonly_fields = ['tags']


#
# Frames
#
class SerialFilter(admin.SimpleListFilter):
    title = 'serial number'
    parameter_name = 'serial'

    def pprint(self, value):
        if value == 0:
            return 'null'

        return '%016X' % value

    def lookups(self, request, model_admin):
        name = self.parameter_name
        values = Metadata.objects.all().values_list('tags', flat=True)
        values = set(value.get(name, 0) for value in values)
        values = [(value, self.pprint(value)) for value in values]
        values = sorted(values, key=lambda x: x[1])
        return values

    def queryset(self, request, queryset):
        name = self.parameter_name
        value = self.value()
        if value:
            if value == 'null':
                return queryset.exclude(metadata__tags__has_key=name)

            value = int(value)
            return queryset.filter(metadata__tags__contains={name: value})

        return queryset

class AddressFilter(SerialFilter):
    title = 'address'
    parameter_name = 'source_addr_long'


@admin.register(Frame)
class FrameAdmin(admin.ModelAdmin):
    list_display = ['time_seconds', 'metadata', 'data']
    readonly_fields = ['time_seconds', 'metadata', 'data']
    list_filter = [SerialFilter, AddressFilter]

    def time_seconds(self, obj):
        return obj.time.strftime("%Y-%m-%d %H:%M:%S %z")

    time_seconds.admin_order_field = 'time'
    time_seconds.short_description = 'Time'
