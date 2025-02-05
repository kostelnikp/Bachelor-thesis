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
    SourceDestinationChordData, HeatmapChartData, PrehladData, dmr_detail_api, get_monitored_frequency, \
    update_monitored_frequency

urlpatterns = [
    path('',  prehlad, name='prehlad'),

    path('admin/', admin.site.urls, name='admin'),

    path('statistiky/', statistiky, name='statistiky'),
    path('prehlad/', prehlad, name='prehlad'),
    path('historia_prevozu/', historia_prevozu, name='historia_prevozu'),
    path('mapa/', mapa, name='mapa'),

    # API endpointy
    path('api/get-monitored-frequency/', get_monitored_frequency, name='get-monitored-frequency'),
    path('api/update-monitored-frequency/', update_monitored_frequency, name='update-monitored-frequency'),



    path('api/pie-chart/', PieChartData.as_view(), name='pie-chart-api'),
    path('api/bar-chart/', BarChartData.as_view(), name='bar-chart-api'),
    path('api/frequency-chart/', FrequencyChartData.as_view(), name='frequency-chart-api'),
    path('api/chord-chart/', SourceDestinationChordData.as_view(), name='chord-chart-api'),
    path('api/heatmap-chart/', HeatmapChartData.as_view(), name='heatmap-chart-api'),
    path('api/prehlad-data/', PrehladData.as_view(), name='prehlad-data'),
    path('api/dmr-detail/<int:event_id>/', dmr_detail_api, name='dmr_detail_api'),

]


