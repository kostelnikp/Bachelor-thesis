"""
URL configuration for dmrserver project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from sdrtrunk.views import statistiky, prehlad, historia_prevozu, mapa, PieChartData, BarChartData, FrequencyChartData, \
    SourceDestinationChordData, HeatmapChartData, PrehladData, get_monitored_frequency, \
    update_monitored_frequency, get_gps_data, ApiDmrHistory, dmr_detail, nastavenia, get_xml_path, get_bat_path, \
    update_xml_path, update_bat_path, start_restart_sdrtrunk, delete_dmr_data

urlpatterns = [
    path('',  prehlad, name='prehlad'),

    path('admin/', admin.site.urls, name='admin'),

    path('statistiky/', statistiky, name='statistiky'),
    path('prehlad/', prehlad, name='prehlad'),
    path('historia_prevozu/', historia_prevozu, name='historia_prevozu'),
    path('mapa/', mapa, name='mapa'),
    path('nastavenia/', nastavenia, name='nastavenia'),

    # API endpointy
    path('api/get-monitored-frequency/', get_monitored_frequency, name='get-monitored-frequency'),
    path('api/update-monitored-frequency/', update_monitored_frequency, name='update-monitored-frequency'),

    path('api/dmr-history/', ApiDmrHistory.as_view(), name='dmr-history-api'),
    path('api/dmr-detail/<int:event_id>/', dmr_detail, name='dmr_detail'),
    path('api/dmr-delete/<int:event_id>/', delete_dmr_data, name='delete_dmr_data'),

    path('api/gps/', get_gps_data, name='get_gps_data'),

    path('api/get-xml-path/', get_xml_path, name='get_xml_path'),
    path('api/update-xml-path/', update_xml_path, name='update_xml_path'),

    path('api/get-bat-path/', get_bat_path, name='get_bat_path'),
    path('api/update-bat-path/', update_bat_path, name='update_bat_path'),

    path('api/start-reset-sdrtrunk/', start_restart_sdrtrunk, name='start-reset-sdrtrunk'),

    path('api/pie-chart/', PieChartData.as_view(), name='pie-chart-api'),
    path('api/bar-chart/', BarChartData.as_view(), name='bar-chart-api'),
    path('api/frequency-chart/', FrequencyChartData.as_view(), name='frequency-chart-api'),
    path('api/chord-chart/', SourceDestinationChordData.as_view(), name='chord-chart-api'),
    path('api/heatmap-chart/', HeatmapChartData.as_view(), name='heatmap-chart-api'),
    path('api/prehlad-data/', PrehladData.as_view(), name='prehlad-data'),

]


