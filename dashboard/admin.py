from django.contrib import admin
from .models import Devices, DeviceList, Gallon

@admin.register(Devices)
class DevicesAdmin(admin.ModelAdmin):
    list_display = ('deviceId', 'status', 'date_created')
    list_filter = ('status',)
    search_fields = ('deviceId', 'status')
    ordering = ('-date_created',)

@admin.register(DeviceList)
class DeviceListAdmin(admin.ModelAdmin):
    list_display = ('deviceId', 'status', 'device_location','limit', 'time_on', 'time_off','is_consumed', 'date_added')
    list_filter = ('status',)

class GallonAdmin(admin.ModelAdmin):
    list_display = ('date_added', 'total_quantity', 'gallons_added', 'gallons_deleted', 'gallons_consumed', 'gallons_remaining')
    search_fields = ('date_added',)

admin.site.register(Gallon, GallonAdmin)
admin.site.site_header = 'Dispencer Admin'
