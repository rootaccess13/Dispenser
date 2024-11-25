from rest_framework import serializers
from .models import Devices, DeviceList

class DevicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devices
        fields = ['deviceId', 'status', 'device_location', 'date_created']

class DeviceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceList
        exclude = ('status',)
class DeviceListUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceList
        fields = ['time_on', 'time_off']

class DeviceListDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceList
        fields = '__all__'
