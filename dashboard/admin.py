from django.contrib import admin
from .models import Devices, DeviceList

@admin.register(Devices)
class DevicesAdmin(admin.ModelAdmin):
    list_display = ('deviceId', 'status', 'date_created')
    list_filter = ('status',)
    search_fields = ('deviceId', 'status')
    ordering = ('-date_created',)

@admin.register(DeviceList)
class DeviceListAdmin(admin.ModelAdmin):
    list_display = ('deviceId', 'status', 'device_location', 'time_on', 'time_off','is_consumed', 'date_added')
    list_filter = ('status',)
