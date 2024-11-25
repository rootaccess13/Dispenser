from __future__ import absolute_import
from celery import shared_task
from dashboard.models import DeviceList
import datetime
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_device_status():
    now = datetime.datetime.now().time()  # Get current time
    devices = DeviceList.objects.all()
    logger.info("Checking device statuses...")
    
    for device in devices:
        if device.time_on and device.time_off:
            if device.time_on <= now <= device.time_off:
                if device.status != True:  # Only save if status is changing
                    logger.info(f"Updating status of {device} to True")
                    device.status = True
            else:
                if device.status != False:  # Only save if status is changing
                    logger.info(f"Updating status of {device} to False")
                    device.status = False
            
            device.save()
        else:
            logger.warning(f"Device {device} does not have valid time_on or time_off.")
