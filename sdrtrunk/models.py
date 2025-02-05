from django.db import models


# Create your models here.

class DMRData(models.Model):
    timestamp = models.DateTimeField(null=True, blank=True)
    duration_s = models.DecimalField(max_digits=10, decimal_places=1, null=True, blank=True)
    protocol = models.CharField(max_length=50)
    event = models.CharField(max_length=100)
    source = models.CharField(max_length=100, null=True, blank=True)
    destination = models.CharField(max_length=100, null=True, blank=True)
    channel_number = models.IntegerField(null=True, blank=True)
    frequency = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    timeslot = models.CharField(max_length=10, null=True, blank=True)
    color_code = models.IntegerField(null=True, blank=True)
    event_id = models.BigIntegerField(null=True, blank=True)
    details = models.TextField()

    def __str__(self):
        formatted_timestamp = self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "N/A"

        return f"{formatted_timestamp} - {self.event} - Freq: {self.frequency} - Event ID: {self.event_id}"

    class Meta:
        verbose_name = "DMR Data"
        verbose_name_plural = "DMR Data"
