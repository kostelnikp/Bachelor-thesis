from datetime import datetime

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django_datatables_view.base_datatable_view import BaseDatatableView

from sdrtrunk.models import DMRData


def historia_prevozu(request):
    dmr_data = DMRData.objects.all()
    return render(request, 'historia_prevozu.html', {'dmr_data': dmr_data})

def available_events(request):
    try:
        events = DMRData.objects.values('event').distinct()
        return JsonResponse({"events": list(events)})
    except Exception as e:
        return JsonResponse({"error": "Nepodarilo sa načítať dostupné udalosti."}, status=500)

class ApiDmrHistory(BaseDatatableView):
    model = DMRData
    columns = ['timestamp', 'duration_s', 'event', 'source', 'destination', 'frequency', 'event_id']
    order_columns = ['timestamp', 'duration_s', 'event', 'source', 'destination', 'frequency', 'event_id']

    def render_column(self, row, column):
        if column == 'timestamp':
            return row.timestamp.strftime('%d.%m.%Y %H:%M:%S') if row.timestamp else ''
        return super().render_column(row, column)

    def get_initial_queryset(self):
        return DMRData.objects.all()

    def filter_queryset(self, qs):
        search_value = self.request.GET.get('search[value]', None)
        if search_value:
            qs = qs.filter(
                Q(timestamp__icontains=search_value) |
                Q(duration_s__icontains=search_value) |
                Q(event__icontains=search_value) |
                Q(source__icontains=search_value) |
                Q(destination__icontains=search_value) |
                Q(frequency__icontains=search_value) |
                Q(event_id__icontains=search_value)
            )

        filter_date_start = self.request.GET.get('start_date', None)
        if filter_date_start:
            try:
                start_date = datetime.strptime(filter_date_start, '%d.%m.%Y')
                qs = qs.filter(timestamp__date__gte=start_date.date())
            except ValueError:
                pass

        filter_date_end = self.request.GET.get('end_date', None)
        if filter_date_end:
            try:
                end_date = datetime.strptime(filter_date_end, '%d.%m.%Y')
                qs = qs.filter(timestamp__date__lte=end_date.date())
            except ValueError:
                pass

        filter_event = self.request.GET.get('filterEvent', None)
        if filter_event:
            qs = qs.filter(event__icontains=filter_event)

        filter_source = self.request.GET.get('filterSource', None)
        if filter_source:
            qs = qs.filter(source__icontains=filter_source)

        filter_destination = self.request.GET.get('filterDestination', None)
        if filter_destination:
            qs = qs.filter(destination__icontains=filter_destination)

        filter_frequency = self.request.GET.get('filterFrequency', None)
        if filter_frequency:
            qs = qs.filter(frequency__icontains=filter_frequency)

        return qs

def dmr_detail(request, event_id):
    dmr_data = get_object_or_404(DMRData, event_id=event_id)
    data = {
        "timestamp": dmr_data.timestamp.strftime("%d.%m.%Y %H:%M:%S"),
        "duration_s": dmr_data.duration_s,
        "event": dmr_data.event,
        "source": dmr_data.source,
        "destination": dmr_data.destination,
        "channel_number": dmr_data.channel_number,
        "frequency": dmr_data.frequency,
        "timeslot": dmr_data.timeslot,
        "color_code": dmr_data.color_code,
        "event_id": dmr_data.id,
        "details": dmr_data.details
    }
    return JsonResponse(data)

@csrf_exempt
def delete_dmr_data(request, event_id):
    try:
        dmr_data = get_object_or_404(DMRData, event_id=event_id)
        dmr_data.delete()
        return JsonResponse({"message": "Udalosť bola úspešne vymazaná."})
    except Exception as e:
        return JsonResponse({"error": "Udalosť sa nepodarilo vymazať."}, status=500)
