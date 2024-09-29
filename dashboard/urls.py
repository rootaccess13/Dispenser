from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name="dashboard"),
    path('api/device-data/', get_device_data, name='get_device_data'),
    path('api/count-devices/', get_total_gallon, name='count_devices'),
    path('api/devices/', DevicesView.as_view(), name='devices'),
    path('api/device-list/', DeviceListView.as_view(), name='device-list'),
    path('api/device-list/<str:device_id>/', DeviceListView.as_view(), name='device-list-status'),
    path('api/update_device/', update_device, name='update_device'),
    path('api/device/update/<str:deviceId>/', DeviceUpdateView.as_view(), name='device-update'),
    path('api/export_device/<str:device_id>/', export_device_pdf, name='export_device_pdf'),

]
