from collections import Counter, defaultdict

from django.db.models import Count
from django.db.models.functions import ExtractWeekDay, ExtractHour
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.decorators import login_required

from sdrtrunk.models import DMRData


@login_required
def statistiky(request):
    return render(request, 'statistiky.html')


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
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        filtered_data = DMRData.objects.all()
        if start_date:
            filtered_data = filtered_data.filter(timestamp__date__gte=start_date)
        if end_date:
            filtered_data = filtered_data.filter(timestamp__date__lte=end_date)

        filtered_data = (
            filtered_data
            .annotate(day_of_week=ExtractWeekDay("timestamp"), hour=ExtractHour("timestamp"))
            .values("day_of_week", "hour")
            .annotate(count=Count("id"))
            .order_by("day_of_week", "hour")
        )

        # Transformácia: (ExtractWeekDay - 2) modulo 7
        heatmap_data = [
            [((entry["day_of_week"] - 2) % 7), entry["hour"], entry["count"]]
            for entry in filtered_data
        ]

        response_data = {
            "data": heatmap_data
        }

        return Response(response_data)
