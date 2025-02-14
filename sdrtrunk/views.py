import os
import platform
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

from django.db.models import Count, Avg, Q
from django.db.models.functions import ExtractHour, ExtractWeekDay
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django_datatables_view.base_datatable_view import BaseDatatableView
from plotly.io._orca import psutil
from rest_framework.response import Response
from rest_framework.utils import json
from rest_framework.views import APIView

from .models import DMRData, GPSData

CONFIG_FILE = "config.json"


def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)


def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)


config = load_config()
XML_FILE_PATH = config.get('XML_FILE_PATH')
SDRTRUNK_PATH = config.get('SDRTRUNK_PATH')


def prehlad(request):
    return render(request, 'prehlad.html')


def historia_prevozu(request):
    dmr_data = DMRData.objects.all()
    return render(request, 'historia_prevozu.html', {'dmr_data': dmr_data})


class ApiDmrHistory(BaseDatatableView):
    model = DMRData
    columns = ['timestamp', 'duration_s', 'event', 'source', 'destination', 'frequency', 'timeslot', 'event_id']
    order_columns = ['timestamp', 'duration_s', 'event', 'source', 'destination', 'frequency', 'timeslot', 'event_id']

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
                Q(timeslot__icontains=search_value) |
                Q(event_id__icontains=search_value)
            )

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
        "frequency": dmr_data.frequency,
        "timeslot": dmr_data.timeslot,
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


def statistiky(request):
    return render(request, 'statistiky.html')


def mapa(request):
    return render(request, 'mapa.html')


def nastavenia(request):
    return render(request, 'nastavenia.html')


def get_xml_path(request):
    if XML_FILE_PATH:
        return JsonResponse({"xml_path": XML_FILE_PATH})
    return JsonResponse({"error": "XML cesta nebola nájdená"}, status=404)


@csrf_exempt
def update_xml_path(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_xml_path = data.get("xml_path")

            if new_xml_path and new_xml_path.endswith(".xml") and os.path.isfile(new_xml_path):
                global XML_FILE_PATH
                XML_FILE_PATH = new_xml_path
                config['XML_FILE_PATH'] = new_xml_path
                save_config(config)
                return JsonResponse({"message": "XML cesta bola úspešne aktualizovaná"})
            else:
                return JsonResponse({"error": "XML cesta je neplatná"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Nepodporovaná metóda"}, status=405)


def get_bat_path(request):
    if SDRTRUNK_PATH:
        return JsonResponse({"bat_path": SDRTRUNK_PATH})
    return JsonResponse({"error": "Bat cesta nebola nájdená"}, status=404)


@csrf_exempt
def update_bat_path(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_bat_path = data.get("bat_path")

            if new_bat_path and new_bat_path.lower().endswith(".bat") and os.path.isfile(new_bat_path):
                global SDRTRUNK_PATH
                SDRTRUNK_PATH = new_bat_path
                config['SDRTRUNK_PATH'] = new_bat_path
                save_config(config)
                return JsonResponse({"message": "Bat cesta bola úspešne aktualizovaná"})
            else:
                return JsonResponse({"error": "Bat cesta je neplatná"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Nepodporovaná metóda"}, status=405)


class PrehladData(APIView):
    """API endpoint pre základné štatistiky prehľadu."""

    def get(self, request):
        data = DMRData.objects.all()
        event_count = data.count()
        last_event = data.order_by('-timestamp').values('timestamp', 'event', 'source', 'destination').first()
        unique_sources = data.values('source').distinct().count()
        unique_destinations = data.values('destination').distinct().count()
        mean_duration = round(data.filter(duration_s__gt=0).aggregate(mean_duration=Avg('duration_s'))['mean_duration'],
                              2)
        most_used_frequency = data.values('frequency').annotate(count=Count('id')).order_by('-count').first()

        if last_event and last_event['timestamp']:
            last_event['timestamp'] = last_event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')

        return Response({
            'event_count': event_count if event_count else None,
            'last_event': last_event if last_event else None,
            'unique_sources': unique_sources if unique_sources else None,
            'unique_destinations': unique_destinations if unique_destinations else None,
            'mean_duration': mean_duration if mean_duration else None,
            'most_used_frequency': most_used_frequency['frequency'] if most_used_frequency else None,

        })


def get_monitored_frequency(request):
    """Načíta monitorovanú frekvenciu zo súboru XML"""
    if not os.path.exists(XML_FILE_PATH):
        return JsonResponse({"error": "Súbor nenájdený"}, status=404)

    tree = ET.parse(XML_FILE_PATH)
    root = tree.getroot()

    frequency_node = root.find(".//source_configuration")
    if frequency_node is not None and "frequency" in frequency_node.attrib:
        frequency = int(frequency_node.attrib["frequency"]) / 1_000_000
        return JsonResponse({"monitored_frequency": f"{frequency:.4f} MHz"})

    return JsonResponse({"error": "Frekvencia nebola nájdená"}, status=404)


@csrf_exempt
def update_monitored_frequency(request):
    """Uloží novú monitorovanú frekvenciu do súboru XML"""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_frequency = float(data.get("frequency")) * 1_000_000

            tree = ET.parse(XML_FILE_PATH)
            root = tree.getroot()

            frequency_node = root.find(".//source_configuration")
            if frequency_node is not None:
                frequency_node.set("frequency", str(int(new_frequency)))
                tree.write(XML_FILE_PATH, encoding="utf-8", xml_declaration=True)

                return JsonResponse({"message": "Frekvencia bola aktualizovaná"})
            else:
                return JsonResponse({"error": "Nepodarilo sa nájsť uzol frekvencie"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Nepodporovaná metóda"}, status=405)


terminal_process = None


@csrf_exempt
def start_restart_sdrtrunk(request):
    global terminal_process

    if request.method == "GET":
        try:
            for process in psutil.process_iter(attrs=['pid', 'name']):
                if "java" in process.info['name'].lower():
                    process.terminate()

            if terminal_process and terminal_process.poll() is None:
                terminal_process.terminate()

            if platform.system() == "Windows":
                terminal_process = subprocess.Popen(["cmd.exe", "/c", f"start cmd /c {SDRTRUNK_PATH}"], shell=True)
            else:
                terminal_process = subprocess.Popen(["gnome-terminal", "--", "bash", "-c", f"{SDRTRUNK_PATH}"])

            return JsonResponse({"message": "SDRTrunk bol úspešne reštartovaný v novom termináli."})

        except Exception:
            return JsonResponse({"error": "Nepodarilo sa reštartovať SDRTrunk."}, status=500)

    return JsonResponse({"error": "Nepodporovaná metóda"}, status=405)


def get_gps_data(request):
    """
    API endpoint na získanie všetkých GPS súradníc z databázy.
    """
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


class PieChartData(APIView):
    """API endpoint pre dáta koláčového grafu (rozdelenie podľa typu eventu)."""

    def get(self, request):
        data = DMRData.objects.all()
        event_data = data.values_list('event', flat=True)
        event_count = Counter(event_data)

        event_count_data = [{'name': event, 'y': count} for event, count in event_count.items()]
        return Response(event_count_data)


class BarChartData(APIView):
    """API endpoint pre dáta stĺpcového grafu (počet udalostí podľa dátumu a eventu)."""

    def get(self, request):
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        filtered_data = DMRData.objects.all()
        if start_date:
            filtered_data = filtered_data.filter(timestamp__date__gte=start_date)
        if end_date:
            filtered_data = filtered_data.filter(timestamp__date__lte=end_date)

        daily_data = filtered_data \
            .values('timestamp__date', 'event') \
            .annotate(count=Count('id')) \
            .order_by('timestamp__date')

        grouped_data = defaultdict(lambda: {"categories": [], "data": []})

        for entry in daily_data:
            date_str = entry["timestamp__date"].strftime('%Y-%m-%d')
            grouped_data[entry["event"]]["categories"].append(date_str)
            grouped_data[entry["event"]]["data"].append(entry["count"])

        all_dates = sorted(set(
            entry["timestamp__date"].strftime('%Y-%m-%d')
            for entry in daily_data
        ))

        response_data = {
            "categories": all_dates,
            "series": []
        }

        for event_name, event_info in grouped_data.items():
            data_array = []
            for date in all_dates:
                if date in event_info["categories"]:
                    idx = event_info["categories"].index(date)
                    data_array.append(event_info["data"][idx])
                else:
                    data_array.append(0)

            response_data["series"].append({
                "name": event_name,
                "data": data_array
            })

        return Response(response_data)


class FrequencyChartData(APIView):
    """
    API endpoint pre dáta (stĺpcového) grafu, zobrazujúci
    na ktorej frekvencii bolo najviac udalostí.
    """

    def get(self, request):
        data = DMRData.objects.all()

        freq_data = data.values('frequency') \
            .annotate(count=Count('id')) \
            .order_by('-count')

        categories = []
        counts = []

        for item in freq_data:
            freq_str = str(item['frequency']) if item['frequency'] is not None else "Neznáma"
            categories.append(freq_str)
            counts.append(item['count'])

        response_data = {
            "categories": categories,
            "counts": counts
        }
        return Response(response_data)


class SourceDestinationChordData(APIView):
    def get(self, request):
        max_links = request.GET.get('max_links', 30)
        try:
            max_links = int(max_links)
            if max_links < 1 or max_links > 100:
                max_links = 30
        except ValueError:
            max_links = 30

        # Načítanie najčastejších spojení už na strane servera
        data = (
            DMRData.objects
            .exclude(source__isnull=True)
            .exclude(destination__isnull=True)
            .values('source', 'destination')
            .annotate(count=Count('id'))
            .order_by('-count')[:max_links]
        )

        sankey_data = [[str(item['source']), str(item['destination']), item['count']] for item in data]

        response_data = {
            "data": sankey_data
        }
        return Response(response_data)


class HeatmapChartData(APIView):
    """API endpoint pre heatmapu zobrazujúcu rozloženie udalostí podľa dňa a hodiny."""

    def get(self, request):
        data = (
            DMRData.objects
            .annotate(day_of_week=ExtractWeekDay("timestamp"), hour=ExtractHour("timestamp"))
            .values("day_of_week", "hour")
            .annotate(count=Count("id"))
            .order_by("day_of_week", "hour")
        )

        # Transformácia: (ExtractWeekDay - 2) modulo 7
        heatmap_data = [
            [((entry["day_of_week"] - 2) % 7), entry["hour"], entry["count"]]
            for entry in data
        ]

        response_data = {
            "data": heatmap_data
        }

        return Response(response_data)
