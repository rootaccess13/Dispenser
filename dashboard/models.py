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
    time_on = models.TimeField(null=True, blank=True)
    time_off = models.TimeField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    is_consumed = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.deviceId} - {self.status}"

class Gallon(models.Model):
    # Fields to store gallon information
    date_added = models.DateField(default=datetime.today)  # Track the date the record is added
    total_quantity = models.IntegerField(default=0)  # Total quantity available in gallons
    gallons_added = models.IntegerField(default=0)  # Track how many gallons have been added
    gallons_deleted = models.IntegerField(default=0)  # Track how many gallons have been deleted
    gallons_consumed = models.IntegerField(default=0)  # Track how many gallons have been consumed
    gallons_remaining = models.IntegerField(default=0)  # Track remaining gallons after operations

    @classmethod
    def get_added_only_records(cls):
        """Get records where only gallons_added was modified."""
        return cls.objects.filter(
            gallons_added__gt=0,
            gallons_deleted=0,
            gallons_consumed=0,
            gallons_remaining=0
        )

    def get_last_added_record_for_instance(self):
        """Get the last record where only gallons_added was modified before the current record."""
        return Gallon.objects.filter(
            date_added__lt=self.date_added,
            gallons_added__gt=0,
            gallons_deleted=0,
            gallons_consumed=0,
            gallons_remaining=0
        ).order_by('-date_added').first()

    def __str__(self):
        return f"Gallon Record for {self.date_added}"

    def update_added(self, quantity):
        """Method to update added gallons."""
        self.gallons_added += quantity
        self.total_quantity += quantity
        self.gallons_remaining += quantity
        self.save()

    def update_deleted(self, quantity):
        """Method to update deleted gallons."""
        if quantity <= self.gallons_remaining:
            self.gallons_deleted += quantity
            self.gallons_remaining -= quantity
            self.save()
        else:
            raise ValueError("Cannot delete more gallons than remaining.")

    def update_consumed(self, quantity):
        """Method to update consumed gallons."""
        if quantity <= self.gallons_remaining:
            self.gallons_consumed += quantity
            self.gallons_remaining -= quantity
            self.save()
        else:
            raise ValueError("Cannot consume more gallons than remaining.")

    def get_remaining(self):
        """Return remaining gallons."""
        return self.gallons_remaining
