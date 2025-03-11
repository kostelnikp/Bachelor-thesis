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
    SourceDestinationChordData, HeatmapChartData, PrehladData, \
    get_gps_data, ApiDmrHistory, dmr_detail, nastavenia, get_bat_path, \
    update_bat_path, start_restart_sdrtrunk, delete_dmr_data, ApiGpsHistory, add_gps_data, \
    delete_gps_data, available_events, load_frequencies, add_monitored_channel, remove_monitored_channel, \
    load_playlist_files, select_xml, get_selected_playlist, get_selected_frequencies

urlpatterns = [
    path('', prehlad, name='prehlad'),

    path('admin/', admin.site.urls, name='admin'),

    # Prehlad
    path('prehlad/', prehlad, name='prehlad'),
    path('api/prehlad-data/', PrehladData.as_view(), name='prehlad-data'),

    # Historia prevozu
    path('historia_prevozu/', historia_prevozu, name='historia_prevozu'),
    path('api/available-events/', available_events, name='available-events-api'),
    path('api/dmr-history/', ApiDmrHistory.as_view(), name='dmr-history-api'),
    path('api/dmr-detail/<int:event_id>/', dmr_detail, name='dmr_detail'),
    path('api/dmr-delete/<int:event_id>/', delete_dmr_data, name='delete_dmr_data'),

    # Mapa
    path('mapa/', mapa, name='mapa'),
    path('api/gps-history/', ApiGpsHistory.as_view(), name='gps-history-api'),
    path('api/gps/', get_gps_data, name='get_gps_data'),
    path('api/gps-data/<int:event_id>/', add_gps_data, name='add_gps_data'),
    path('api/gps-delete/<int:event_id>/', delete_gps_data, name='delete_gps_data'),

    # Statistiky
    path('statistiky/', statistiky, name='statistiky'),
    path('api/pie-chart/', PieChartData.as_view(), name='pie-chart-api'),
    path('api/bar-chart/', BarChartData.as_view(), name='bar-chart-api'),
    path('api/frequency-chart/', FrequencyChartData.as_view(), name='frequency-chart-api'),
    path('api/chord-chart/', SourceDestinationChordData.as_view(), name='chord-chart-api'),
    path('api/heatmap-chart/', HeatmapChartData.as_view(), name='heatmap-chart-api'),

    # Nastavenia
    path('nastavenia/', nastavenia, name='nastavenia'),
    path('api/get-bat-path/', get_bat_path, name='get_bat_path'),
    path('api/update-bat-path/', update_bat_path, name='update_bat_path'),
    path('api/start-reset-sdrtrunk/', start_restart_sdrtrunk, name='start-reset-sdrtrunk'),
    path('api/load-frequencies/', load_frequencies, name='load_frequencies'),
    path('api/add-frequency/', add_monitored_channel, name='add-frequency'),
    path('api/remove-frequency/', remove_monitored_channel, name='remove-frequency'),
    path('api/load-xml/', load_playlist_files, name='load-xml'),
    path('api/select-xml/', select_xml, name='select-xml'),
    path('api/get-selected-playlist/', get_selected_playlist, name='get-selected-playlist'),
    path('api/get-selected-frequencies/', get_selected_frequencies, name='get-selected-frequencies'),

]
