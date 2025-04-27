import binascii
import re
from datetime import datetime
from decimal import Decimal

from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django_datatables_view.base_datatable_view import BaseDatatableView
from rest_framework.utils import json
from django.contrib.auth.decorators import login_required

from sdrtrunk.models import DMRData, GPSData


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
        known_types = ["DEFINED SHORT DATA PACKET", "UNKNOWN PACKET", "UDP", "ARS", "IP", "PORT"]
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

        filter_timeslot = self.request.GET.get('filterTimeslot', None)
        if filter_timeslot and filter_timeslot != '':
            qs = qs.filter(timeslot=filter_timeslot)

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
                if decoded_details.startswith("Chyba pri dekódovaní"):
                    return JsonResponse({'error': decoded_details}, status=400)
                return JsonResponse({'decoded_details': decoded_details})
            else:
                return JsonResponse({'error': 'Neboli poskytnuté potrebné údaje'}, status=400)
        except Exception as e:
            return JsonResponse({'error': f'Chyba: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Neplatná metóda požiadavky'}, status=405)


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
        return f"Chyba pri dekódovaní: {str(e)}"

def decode_unknown_packet_function(data, decodeType, startPos, endPos):
    try:
        decodeType = decodeType.strip().lower()
        
        clean_data = ''.join(filter(lambda c: c.upper() in '0123456789ABCDEF', data))
        
        if not clean_data:
            return "Chyba pri dekódovaní: Neplatné hexadecimálne dáta"
        
        try:
            byte_data = binascii.unhexlify(clean_data)
        except binascii.Error:
            if len(clean_data) % 2 != 0:
                clean_data += '0'
                try:
                    byte_data = binascii.unhexlify(clean_data)
                except binascii.Error:
                    return "Chyba pri dekódovaní: Neplatné hexadecimálne dáta"
            else:
                return "Chyba pri dekódovaní: Neplatné hexadecimálne dáta"

        try:
            if isinstance(endPos, str) and endPos.startswith('-'):
                end_byte = len(byte_data) + int(endPos)
            else:
                end_byte = int(endPos) if endPos != "" and endPos is not None else len(byte_data)
                
            start_byte = int(startPos) if startPos != "" and startPos is not None else 0
            
            if start_byte < 0:
                start_byte = 0
            if end_byte > len(byte_data):
                end_byte = len(byte_data)
            if start_byte >= end_byte:
                return "Chyba pri dekódovaní: Neplatný rozsah indexov (začiatok >= koniec)"
                
            byte_segment = byte_data[start_byte:end_byte]
        except (ValueError, TypeError):
            return "Chyba pri dekódovaní: Neplatné indexy"
        
        if not byte_segment:
            return "Nič na dekódovanie v zadanom rozsahu"
            
        try:
            if decodeType == 'ascii':
                result = byte_segment.decode("ascii", errors="replace")
            elif decodeType == 'utf-8':
                result = byte_segment.decode("utf-8", errors="replace")
            elif decodeType == 'utf-16':
                result = byte_segment.decode("utf-16", errors="replace")
            else:
                return "Nepodporované kódovanie"
                
            if all(c == '�' for c in result if c not in ' \t\n\r'):
                return "Nepodarilo sa dekódovať: žiadne platné znaky v danom kódovaní"
            
                
            return result
        except Exception as e:
            return f"Chyba pri dekódovaní: {str(e)}"
    except Exception as e:
        return f"Chyba pri dekódovaní: {str(e)}"


def parse_gprmc_data(gprmc_text):
    try:
        gprmc_text = gprmc_text.replace('\x00', '').replace('\\u0000', '')
        gprmc_text = ''.join(c for c in gprmc_text if c.isprintable() or c.isspace())
        
        
        gprmc_pattern = r'\$GPRMC,([^*]+)\*?[A-F0-9]{0,2}'
        match = re.search(gprmc_pattern, gprmc_text)
        
        if not match:
            alt_pattern = r'GPRMC,([0-9]+\.[0-9]+,A,[0-9.]+,[NS],[0-9.]+,[EW])'
            alt_match = re.search(alt_pattern, gprmc_text)
            if alt_match:
                gprmc_parts = alt_match.group(1).split(',')
            else:
                return None
            
        parts = match.group(1).split(',')
        
       
        if len(parts) < 9 or parts[1] != 'A':
            return None
            
        
        lat = parts[2]
        lat_dir = parts[3] 
        
        lon = parts[4]
        lon_dir = parts[5] 
        
        print(f"Extracted coords: Lat={lat}{lat_dir}, Lon={lon}{lon_dir}")
        
       
        try:
            lat_deg = float(lat[:2])
            lat_min = float(lat[2:])
            latitude = lat_deg + (lat_min / 60.0)
            if lat_dir == 'S':
                latitude = -latitude
                
           
            lon_deg = float(lon[:3])
            lon_min = float(lon[3:])
            longitude = lon_deg + (lon_min / 60.0)
            if lon_dir == 'W':
                longitude = -longitude
                
        except (ValueError, IndexError) as e:
            return None
            
        return {
            'latitude': Decimal(str(latitude)),
            'longitude': Decimal(str(longitude)),
            'is_valid': True
        }
    except Exception as e:
        print(f"GPRMC parsing error: {e}")
        return None

@csrf_exempt
def create_gps_entry(request, event_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Neplatná metóda požiadavky'}, status=405)
        
    try:
        data = json.loads(request.body)
        gprmc_data = data.get('gprmc_data')
        
        if not gprmc_data:
            return JsonResponse({'error': 'Chýbajúce GPRMC dáta'}, status=400)
        
        print(f"Prijaté GPRMC dáta: {gprmc_data}")
        
        parsed_gps = parse_gprmc_data(gprmc_data)
        
        if not parsed_gps:
            gprmc_pattern = r'(\$GPRMC,[^*]+\*[A-F0-9]{2})'
            match = re.search(gprmc_pattern, gprmc_data)
            if match:
                clean_gprmc = match.group(1)
                print(f"Skúšam s vyčisteným GPRMC: {clean_gprmc}")
                parsed_gps = parse_gprmc_data(clean_gprmc)
        
        if not parsed_gps or not parsed_gps.get('is_valid'):
            return JsonResponse({'error': 'Nepodarilo sa získať platné GPS súradnice z dát'}, status=400)
            
        latitude = parsed_gps.get('latitude')
        longitude = parsed_gps.get('longitude')
        
        print(f"Spracované súradnice: Lat={latitude}, Lon={longitude}")
            
        dmr_data = get_object_or_404(DMRData, event_id=event_id)
        
        existing_gps = GPSData.objects.filter(dmr_data=dmr_data).first()
        if existing_gps:
            existing_gps.latitude = latitude
            existing_gps.longitude = longitude
            existing_gps.save()
            return JsonResponse({
                'message': 'GPS dáta úspešne aktualizované',
                'latitude': str(latitude),
                'longitude': str(longitude)
            })
        else:
            gps_entry = GPSData.objects.create(
                dmr_data=dmr_data,
                latitude=latitude,
                longitude=longitude
            )
            return JsonResponse({
                'message': 'GPS dáta boli úspešne pridané do mapy',
                'latitude': str(latitude),
                'longitude': str(longitude)
            })
            
    except Exception as e:
        print(f"Chyba v create_gps_entry: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Nepodarilo sa pridať GPS súradnice: {str(e)}'}, status=500)

