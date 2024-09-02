from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard, name="dashboard"),
    path('api/device-data/', get_device_data, name='get_device_data'),
    path('api/count-devices/', get_total_gallon, name='count_devices'),
    path('api/devices/', DevicesView.as_view(), name='devices'),
    path('api/device-list/', DeviceListView.as_view(), name='device-list')
]