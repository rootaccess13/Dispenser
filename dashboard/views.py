from django.shortcuts import render
from .firebase_helper import firebase_get
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Devices, DeviceList
from .serializers import DevicesSerializer, DeviceListSerializer
from django.db.models import OuterRef, Subquery
from datetime import datetime
from django.contrib.auth.decorators import login_required


def get_device_data(request):
    devicespath = '/devices/'
    data = firebase_get(devicespath)
    return JsonResponse(data)

def get_total_gallon(request):
    devicespath = '/devices/'
    data = firebase_get(devicespath)

    if data:
        total_devices = len(data)
    else:
        total_devices = 0

    return JsonResponse({'total_devices': total_devices})

@login_required
def dashboard(request):
    latest_records = Devices.objects.filter(deviceId=OuterRef('deviceId')).order_by('-date_created')
    device_list = DeviceList.objects.all()
    consumed = DeviceList.objects.all().filter(is_consumed=True)
    # Get the latest record per deviceId
    unique_devices = Devices.objects.filter(
        id__in=Subquery(latest_records.values('id')[:1])
    )
    print(unique_devices)
    context = {
        'device_count': device_list.count(),
        'devices': unique_devices,
        'device_consumed': consumed.count()

    }
    return render(request, 'dashboard/index.html', context)



class DevicesView(APIView):
    def post(self, request):
        # Extract data from request
        data = request.data
        
        # Check if 'status' is 'HIGH' and set date_consumed accordingly
        if data.get('status') == 'HIGH':
            data['date_consumed'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Ensure date_consumed is not set if status is not 'HIGH'
            data['date_consumed'] = None
        
        # Create serializer instance with the updated data
        serializer = DevicesSerializer(data=data)
        print(data)  # For debugging purposes

        # Validate and save data
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Status updated successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeviceListView(APIView):
    def post(self, request):
        serializer = DeviceListSerializer(data=request.data)
        if serializer.is_valid():
            # Extract the deviceId from the request data
            device_id = serializer.validated_data.get('deviceId')
            
            # Check if a device with this deviceId already exists
            if DeviceList.objects.filter(deviceId=device_id).exists():
                return Response({"message": "Device already recorded"}, status=status.HTTP_400_BAD_REQUEST)
            
            # If the device does not exist, save the new device
            serializer.save()
            return Response({"message": "Device added successfully"}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request, device_id=None):
        # Check if a deviceId is provided in the URL
        if not device_id:
            return Response("Device ID is required", status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Fetch the device from the database
            device = DeviceList.objects.get(deviceId=device_id)
        except DeviceList.DoesNotExist:
            return Response("Device not found", status=status.HTTP_404_NOT_FOUND)
        
        # Return the status value directly
        return Response(str(device.status), content_type='text/plain', status=status.HTTP_200_OK)
