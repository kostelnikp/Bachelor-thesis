from django.db.models import Count, Avg
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from sdrtrunk.models import DMRData


def prehlad(request):
    return render(request, 'prehlad.html')

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

def currently_monitored_frequencies(request):
    from sdrtrunk.views.nastavenia import get_selected_frequencies
    return get_selected_frequencies(request)