from django.shortcuts import render, redirect
from .firebase_helper import firebase_get
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Devices, DeviceList
from .serializers import DevicesSerializer, DeviceListSerializer
from django.db.models import OuterRef, Subquery
from datetime import datetime, time
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from django.shortcuts import get_object_or_404
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

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
        'device_list': device_list,
        'device_count': device_list.count(),
        'devices': unique_devices,
        'device_consumed': unique_devices.count()

    }
    return render(request, 'dashboard/index.html', context)

@require_POST
def update_device(request):
    device_id = request.POST.get('device_id')
    location = request.POST.get('location')
    time_on_str = request.POST.get('time_on')
    time_off_str = request.POST.get('time_off')
    turn_off = request.POST.get('turn_off_checkbox') == 'on'
    
    # Initialize time variables
    time_on = None
    time_off = None
    
    try:
        # Convert time strings to time objects
        if time_on_str:
            time_on = datetime.strptime(time_on_str, "%H:%M").time()
        if time_off_str:
            time_off = datetime.strptime(time_off_str, "%H:%M").time()
    except ValueError as e:
        # Handle invalid time format
        raise ValidationError(f"Invalid time format: {e}")

    try:
        # Retrieve and update the device record
        device = DeviceList.objects.get(deviceId=device_id)
        if location:
            device.device_location = location
        if time_on:
            device.time_on = time_on
        if time_off:
            device.time_off = time_off
        if turn_off:
            device.status = False  # Assuming False means turned off
        
        device.save()
    except DeviceList.DoesNotExist:
        raise ValidationError("Device not found.")

    return redirect('dashboard')  # Adjust the redirect URL as needed

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


class DeviceUpdateView(APIView):
    def put(self, request, deviceId):
        try:
            device = DeviceList.objects.get(deviceId=deviceId)
        except DeviceList.DoesNotExist:
            return Response({"error": "Device not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DeviceListSerializer(device, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def export_device_pdf(request, device_id):
    # Try to get the specific device object
    device = Devices.objects.filter(deviceId=device_id).first()
    device_info = DeviceList.objects.filter(deviceId=device_id).first()

    if not device:
        return HttpResponse("Device not found.", status=404)

    if not device_info:
        return HttpResponse("DeviceList entry not found.", status=404)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{device.deviceId}-{datetime.now().strftime("%d-%m-%Y")}.pdf"'


    pdf = SimpleDocTemplate(response, pagesize=landscape(letter))

    elements = []

    styles = getSampleStyleSheet()
    
    # Add Header
    header = Paragraph("<b>Dispencer Generated Data</b>", styles['Title'])
    elements.append(header)
    elements.append(Spacer(1, 10))  # Add space after the header

    # Device information with background color
    device_infos = [
        Paragraph(f"<b>Device ID:</b> {device_info.deviceId}", styles['Normal']),
        Paragraph(f"<b>Status:</b> {'On' if device_info.status else 'Off'}", styles['Normal']),
        Paragraph(f"<b>Location:</b> {device_info.device_location}", styles['Normal']),
        Paragraph(f"<b>Date Power On:</b> {device_info.time_on if device_info.time_on else 'N/A'}", styles['Normal']),
        Paragraph(f"<b>Date Power Off:</b> {device_info.time_off if device_info.time_off else 'N/A'}", styles['Normal'])
    ]

    # Background color for device_infos
    for info in device_infos:
        info_background = Paragraph(f"<font color='{colors.white}'>{info.text}</font>", styles['Normal'])
        elements.append(Spacer(1, 5))  # Add space between entries
        elements.append(info_background)

    # Add a colored box around device information
    device_info_table_data = [[info for info in device_infos]]
    device_info_table = Table(device_info_table_data, colWidths='*')
    
    # Add styling to the device info table
    device_info_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ])
    device_info_table.setStyle(device_info_style)

    elements.append(device_info_table)
    elements.append(Spacer(1, 10))  # Add space before the main table

    # Fetch all devices for the table
    devices = Devices.objects.all().filter(deviceId=device_id).values_list('deviceId', 'status', 'device_location', 'date_created', 'date_consumed')
    
    data = [['Device ID', 'Status', 'Location', 'Date Created', 'Date Consumed']]
    for device in devices:
        data.append(list(device))

    # Create a Table
    table = Table(data)
    
    # Add styling to the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)

    # Add the table to the elements
    elements.append(table)

    # Build the PDF
    pdf.build(elements)

    return response
