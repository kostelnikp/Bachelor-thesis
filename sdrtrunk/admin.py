from django.contrib import admin
from .models import DMRData, GPSData

# Register your models here.

admin.site.register(DMRData)
admin.site.register(GPSData)
