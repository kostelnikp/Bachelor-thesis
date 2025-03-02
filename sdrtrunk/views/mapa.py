from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django_datatables_view.base_datatable_view import BaseDatatableView

from sdrtrunk.models import GPSData


def mapa(request):
    return render(request, 'mapa.html')

class ApiGpsHistory(BaseDatatableView):
    model = GPSData
    columns = ['timestamp', 'source', 'destination', 'latitude', 'longitude', 'event_id']
    order_columns = ['dmr_data__timestamp', 'dmr_data__source', 'dmr_data__destination', 'latitude', 'longitude', 'dmr_data__event_id']

    def render_column(self, row, column):
        if column == 'timestamp':
            return row.dmr_data.timestamp.strftime('%d.%m.%Y %H:%M:%S') if row.dmr_data.timestamp else ''
        elif column == 'source':
            return row.dmr_data.source if row.dmr_data.source else ''
        elif column == 'destination':
            return row.dmr_data.destination if row.dmr_data.destination else ''
        elif column == 'event_id':
            return row.dmr_data.event_id if row.dmr_data.event_id else ''
        return super().render_column(row, column)

    def get_initial_queryset(self):
        return GPSData.objects.select_related('dmr_data').all()

    def filter_queryset(self, qs):
        filter_source = self.request.GET.get('filterSource', None)
        if filter_source:
            qs = qs.filter(dmr_data__source__icontains=filter_source)

        filter_destination = self.request.GET.get('filterDestination', None)
        if filter_destination:
            qs = qs.filter(dmr_data__destination__icontains=filter_destination)

        return qs

@csrf_exempt
def add_gps_data(request, event_id):
    try:
        gps_data = GPSData.objects.select_related('dmr_data').get(dmr_data__event_id=event_id)
        data = {
            "event_id": gps_data.dmr_data.event_id,
            "source": gps_data.dmr_data.source if gps_data.dmr_data else None,
            "destination": gps_data.dmr_data.destination if gps_data.dmr_data else None,
            "latitude": gps_data.latitude,
            "longitude": gps_data.longitude,
            "timestamp": gps_data.dmr_data.timestamp.strftime('%d.%m.%Y %H:%M:%S') if gps_data.dmr_data else None,
            "details": gps_data.dmr_data.details
        }
        return JsonResponse(data)
    except GPSData.DoesNotExist:
        return JsonResponse({"error": "GPS dáta sa nepodarilo načítať z databázy."}, status=500)

@csrf_exempt
def delete_gps_data(request, event_id):
    try:
        gps_data = get_object_or_404(GPSData, dmr_data__event_id=event_id)
        gps_data.delete()
        return JsonResponse({"message": "Udalosť bola úspešne vymazaná."})
    except Exception as e:
        return JsonResponse({"error": "Udalosť sa nepodarilo vymazať."}, status=500)

def get_gps_data(request):
    """
    API endpoint na získanie všetkých GPS súradníc z databázy.
    """
    try:
        gps_records = GPSData.objects.select_related("dmr_data").all()

        gps_data = [
            {
                "latitude": gps.latitude,
                "longitude": gps.longitude,
                "event_id": gps.dmr_data.event_id,
                "source": gps.dmr_data.source,
                "destination": gps.dmr_data.destination,
                "timestamp": gps.dmr_data.timestamp.strftime("%Y-%m-%d %H:%M:%S") if gps.dmr_data.timestamp else "",
                "details": gps.dmr_data.details
            }
            for gps in gps_records
        ]

        return JsonResponse({"gps_data": gps_data})
    except Exception as e:
        return JsonResponse({"error": "GPS dáta sa nepodarilo načítať z databázy."}, status=500)
