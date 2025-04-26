import binascii
from datetime import datetime

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django_datatables_view.base_datatable_view import BaseDatatableView
from rest_framework.utils import json
from django.contrib.auth.decorators import login_required

from sdrtrunk.models import DMRData


@login_required
def historia_prevozu(request):
    dmr_data = DMRData.objects.all()
    return render(request, 'historia_prevozu.html', {'dmr_data': dmr_data})


def available_events(request):
    try:
        events = DMRData.objects.values('event').distinct()
        return JsonResponse({"events": list(events)})
    except Exception as e:
        return JsonResponse({"error": "Nepodarilo sa načítať dostupné udalosti."}, status=500)


def available_detail_types(request):
    try:
        known_types = ["DEFINED SHORT DATA PACKET", "UNKNOWN PACKET", "UDP", "ARS"]
        return JsonResponse({"detail_types": known_types})
    except Exception as e:
        return JsonResponse({"error": "Nepodarilo sa načítať dostupné typy detailov."}, status=500)


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
            
        filter_details = self.request.GET.get('filterDetails', None)
        if filter_details:
            qs = qs.filter(details__icontains=filter_details)

        # Filtrování podle délky trvání
        min_duration = self.request.GET.get('minDuration', None)
        if min_duration and min_duration != '':
            try:
                min_duration_float = float(min_duration)
                qs = qs.filter(duration_s__gte=min_duration_float)
            except (ValueError, TypeError):
                pass

        max_duration = self.request.GET.get('maxDuration', None)
        if max_duration and max_duration != '':
            try:
                max_duration_float = float(max_duration)
                qs = qs.filter(duration_s__lte=max_duration_float)
            except (ValueError, TypeError):
                pass

        # Filtrování podle timeslot
        filter_timeslot = self.request.GET.get('filterTimeslot', None)
        if filter_timeslot and filter_timeslot != '':
            qs = qs.filter(timeslot=filter_timeslot)

        # Filtrování podle color code
        filter_color_code = self.request.GET.get('filterColorCode', None)
        if filter_color_code and filter_color_code != '':
            qs = qs.filter(color_code=filter_color_code)

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


@csrf_exempt
def decode_short_data_packet(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            details = data.get('details')
            if details:
                decoded_details = decode_short_data_packet_function(details)
                return JsonResponse({'decoded_details': decoded_details})
            else:
                return JsonResponse({'error': 'No details provided'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def decode_unknown_packet(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            details = data.get('details')
            decode_type = data.get('decodeType')
            start_pos = data.get('startPos')
            end_pos = data.get('endPos')

            if details and decode_type and start_pos is not None and end_pos is not None:
                decoded_details = decode_unknown_packet_function(details, decode_type, start_pos, end_pos)
                if decoded_details == "Chyba pri dekódovaní":
                    return JsonResponse({'error': decoded_details}, status=400)
                return JsonResponse({'decoded_details': decoded_details})
            else:
                return JsonResponse({'error': 'No details provided'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def decode_short_data_packet_function(data):
    out = b''
    delta = 36  # block shift (extra checksum at each block?)
    block = 32  # maximum text block size
    start = 4  # initial skip
    end = 8  # end offset (block checksum + full checksum?)

    i = start
    try:
        while i < len(data):
            out += binascii.unhexlify(data[i:min(i + block, len(data) - end)])
            i += delta
        return str(out, "utf-16-be")
    except Exception as e:
        return f"Chyba pri dekódovaní"

def decode_unknown_packet_function(data, decodeType, startPos, endPos):
    try:
        decodeType = decodeType.strip().lower()
        clean_data = ''.join(filter(str.isalnum, data))
        byte_data = binascii.unhexlify(clean_data)
        start_byte = int(startPos) if startPos != "" and startPos is not None else 0
        end_byte = int(endPos) if endPos != "" and endPos is not None else len(byte_data)
        byte_segment = byte_data[start_byte:end_byte]
        if decodeType == 'ascii':
            return byte_segment.decode("ascii", errors="replace")
        elif decodeType == 'utf-8':
            return byte_segment.decode("utf-8", errors="replace")
        elif decodeType == 'utf-16':
            return byte_segment.decode("utf-16", errors="replace")
        else:
            return "Nepodporované kódovanie"
    except Exception:
        return "Chyba pri dekódovaní"

