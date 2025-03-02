from django.contrib import admin
from .models import DMRData, GPSData

class DMRDataAdmin(admin.ModelAdmin):
    list_filter = ('event',)

admin.site.register(DMRData, DMRDataAdmin)
admin.site.register(GPSData)
