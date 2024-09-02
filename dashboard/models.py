from django.db import models
from datetime import datetime

class Devices(models.Model):
    deviceId = models.CharField(max_length=100)
    status = models.CharField(max_length=10)
    device_location = models.CharField(default="Not Set", max_length=255, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_consumed = models.DateTimeField(blank=True, null=True)
    is_standby = models.BooleanField(default=False)
    is_consumed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.deviceId} - {self.status} - {self.date_created}"

    def save(self, *args, **kwargs):
        # Check if status is 'LOW' and set date_consumed
        if self.status == 'LOW':
            self.date_consumed = datetime.now()
        else:
            self.date_consumed = None
        
        # Call the parent class's save method to save the instance
        super().save(*args, **kwargs)

class DeviceList(models.Model):
    deviceId = models.CharField(max_length=100)
    status = models.BooleanField(default=False)
    device_location = models.CharField(default="Not Set", max_length=255, blank=True, null=True)
    time_on = models.DateTimeField(blank=True, null=True)
    time_off = models.DateTimeField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    is_consumed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.deviceId} - {self.status}"