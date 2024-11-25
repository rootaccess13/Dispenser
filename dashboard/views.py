from django.shortcuts import render, redirect
from .firebase_helper import firebase_get
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Devices, DeviceList
from .serializers import DevicesSerializer, DeviceListSerializer
from django.db.models import OuterRef, Subquery
from datetime import datetime, time, date, timedelta
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
from .serializers import DeviceListDataSerializer
from rest_framework.decorators import api_view
from .models import Gallon
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from django.core.paginator import Paginator


def add_gallon(request):
    if request.method == 'POST':
        try:
            # Get the form data
            quantity = int(request.POST.get('quantity'))
            date_added = request.POST.get('date_added')  # Get the date from the form
            
            # Parse the date in MM/DD/YYYY format
            date_added = datetime.strptime(date_added, '%m/%d/%Y')  # Parse the date

            gallon = Gallon(
                total_quantity=0,
                date_added=date_added,
                gallons_consumed=0,
                gallons_added=quantity,
                gallons_deleted=0,
                gallons_remaining=0
            )
            gallon.save()

            # Success message
            messages.success(request, "Gallons successfully added!")

            return redirect('inventory')

        except Exception as e:
            # Error message
            messages.error(request, f"Error: {str(e)}")

    return render(request, 'your_template.html')

def delete_gallon(request):
    if request.method == "POST":
        try:
            # Get form data
            date_deleted = request.POST.get('date_deleted')
            quantity_deleted = int(request.POST.get('quantity_deleted'))

            # Parse date_deleted from string to datetime
            date_deleted = datetime.strptime(date_deleted, '%m/%d/%Y').date()

            gallon = Gallon(
                total_quantity=0,
                date_added=date_deleted,
                gallons_consumed=0,
                gallons_added=0,
                gallons_deleted=quantity_deleted,
                gallons_remaining=0
            )
            gallon.save()

            # Success message
            messages.success(request, "Gallons successfully deleted!")

            return redirect('inventory')

        except Exception as e:
            # Error message
            messages.error(request, f"Error: {str(e)}")

    return JsonResponse({"status": "error", "message": "Invalid request"})

@api_view(['GET'])
def get_device_by_id(request, deviceId):
    try:
        device = DeviceList.objects.get(deviceId=deviceId)
    except DeviceList.DoesNotExist:
        return Response({"error": "Device not found"}, status=404)

    serializer = DeviceListDataSerializer(device)
    return Response(serializer.data)

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
        'device_consumed': unique_devices.count(),
        'consumed': consumed

    }
    return render(request, 'dashboard/index.html', context)

def about(request):
    return render(request, 'dashboard/about.html')

def usepage(request):
    return render(request, 'dashboard/use.html')

def developers(request):
    return render(request, 'dashboard/developers.html')

def inventory(request):
    # Get today's date
    today = date.today()

    # Fetch all records from today
    gallons_today = Gallon.objects.filter(date_added=today)

    # Initialize variables to calculate total remaining, total consumed, total added, and total deleted gallons
    total_remaining_gallons = 0
    total_consumed_gallons = 0
    total_added_gallons = 0
    total_deleted_gallons = 0  # Variable to track total deleted gallons

    for gallon in gallons_today:
        # Calculate remaining gallons for each record
        remaining_gallons = gallon.total_quantity - (gallon.gallons_deleted + gallon.gallons_consumed)
        gallon.gallons_remaining = remaining_gallons  # You could save this value to the database if needed
        total_remaining_gallons += remaining_gallons + gallon.gallons_added

        # Add the current record's consumed gallons to total_consumed_gallons
        total_consumed_gallons += gallon.gallons_consumed

        # Add the current record's added gallons to total_added_gallons
        total_added_gallons += gallon.gallons_added

        # Add the current record's deleted gallons to total_deleted_gallons
        total_deleted_gallons += gallon.gallons_deleted

        # Calculate the total (sum of total_quantity and gallons_added)
        gallon.total = gallon.total_quantity + gallon.gallons_added
        
        # Calculate the final inventory
        gallon.final_inventory = gallon.total_quantity - gallon.gallons_consumed - gallon.gallons_deleted + gallon.gallons_added
        
        # If final_inventory is negative, set it to 0
        if gallon.final_inventory < 0:
            gallon.final_inventory = 0

    # Pagination: Show 10 records per page
    paginator = Paginator(gallons_today, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Query the LogEntry model to get all actions related to Gallon objects
    gallon_content_type = ContentType.objects.get_for_model(Gallon)
    log_entries = LogEntry.objects.filter(content_type=gallon_content_type).order_by('-action_time')

    context = {
        'gallons_today': page_obj,
        'total_remaining_gallons': total_remaining_gallons,  # Total remaining gallons for the day
        'total_consumed_gallons': total_consumed_gallons,    # Total consumed gallons for the day
        'total_added_gallons': total_added_gallons,          # Total added gallons for the day
        'total_deleted_gallons': total_deleted_gallons,      # Total deleted gallons for the day
        'log_entries': log_entries  # Pass the action history to the template
    }

    return render(request, 'admin/inventory.html', context)

def logs(request):
    gallon_content_type = ContentType.objects.get_for_model(Gallon)
    log_entries = LogEntry.objects.filter(content_type=gallon_content_type).order_by('-action_time')
    context = {
        'log_entries': log_entries
    }
    return render(request, 'admin/logs.html', context)

def summary_report(request):
    return render(request, 'admin/summary_report.html')

def added_gallons(request):
    added_only_records = Gallon.get_added_only_records()
    context = {
        'added_only_records': added_only_records
    }
    return render(request, 'admin/added_gallons.html', context)


def adminpage(request):
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
    return render(request, 'admin/admin.html', context)

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
            
            # Check the status and convert to "True" or "False" (string)
            if device.status == True:
                device.status = "True"
            elif device.status == False:
                device.status = "False"
        except DeviceList.DoesNotExist:
            return Response("Device not found", status=status.HTTP_404_NOT_FOUND)
    
    # Return the status value directly
        return Response(device.status, content_type='text/plain', status=status.HTTP_200_OK)



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


def summary_report(request):
    # Get the selected date range from GET parameters (defaults to '30' for the last 30 days)
    date_range = request.GET.get('date_range', '30')  # Default to last 30 days if nothing is selected

    # Get today's date
    today = date.today()

    # Calculate the start date based on the selected date range
    if date_range == '0':  # Today
        start_date = today  # Only today
    elif date_range == '1':  # Last day
        start_date = today - timedelta(days=1)
    elif date_range == '7':  # Last 7 days
        start_date = today - timedelta(days=7)
    elif date_range == '30':  # Last 30 days
        start_date = today - timedelta(days=30)
    elif date_range == '365':  # Last year
        start_date = today - timedelta(days=365)
    else:
        start_date = today  # Default to today if no valid date range is selected

    # Filter records by date range
    gallons_today = Gallon.objects.filter(date_added__gte=start_date)

    # Add a 'total' field to each entry in gallons_today (sum of total_quantity and gallons_added)
    for data in gallons_today:
        # Calculate the total (sum of total_quantity and gallons_added)
        data.total = data.total_quantity + data.gallons_added
        
        # Calculate the final inventory
        data.final_inventory = data.total_quantity - data.gallons_consumed - data.gallons_deleted + data.gallons_added
        
        # If final_inventory is negative, set it to 0
        if data.final_inventory < 0:
            data.final_inventory = 0

    # Pagination logic
    paginator = Paginator(gallons_today, 10)  # Show 10 records per page
    page_number = request.GET.get('page')  # Get the page number from the URL
    page_obj = paginator.get_page(page_number)  # Get the page object

    # Pass the selected date range and page_obj to the context
    context = {
        'page_obj': page_obj,
        'date_range': date_range,
        'gallons_today': gallons_today
    }

    return render(request, 'admin/summary_report.html', context)
