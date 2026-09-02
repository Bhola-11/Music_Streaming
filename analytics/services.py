"""
Analytics Aggregation Service: Global Telemetry Rollup & Real-Time Performance Analytics.
"""
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count
from .models import DailyPlatformMetric, StreamGeoHeatmap
from music.models import Song
from artists.models import Artist
from player.models import ListeningHistory
from accounts.models import User


class AnalyticsAggregationService:
    """
    Computes platform-wide metrics and aggregates streaming stats.
    """

    @classmethod
    def generate_today_snapshot(cls) -> DailyPlatformMetric:
        today = timezone.now().date()
        
        streams_count = ListeningHistory.objects.filter(played_at__date=today).count()
        unique_users = ListeningHistory.objects.filter(played_at__date=today).values('user').distinct().count()
        new_users = User.objects.filter(date_joined__date=today).count()
        new_songs = Song.objects.filter(created_at__date=today).count()

        # Estimate bandwidth: approx 10MB per stream
        bandwidth_gb = Decimal(streams_count * 10) / Decimal(1024)
        royalty_usd = Decimal(streams_count) * Decimal('0.0045')

        metric, created = DailyPlatformMetric.objects.update_or_create(
            date=today,
            defaults={
                'total_streams': streams_count,
                'unique_listeners': unique_users,
                'new_users_registered': new_users,
                'new_tracks_uploaded': new_songs,
                'bandwidth_served_gb': round(bandwidth_gb, 2),
                'royalty_accrued_usd': round(royalty_usd, 2),
            }
        )
        return metric

    @classmethod
    def get_platform_overview(cls):
        return {
            'total_users': User.objects.count(),
            'total_artists': Artist.objects.count(),
            'total_songs': Song.objects.count(),
            'total_streams_all_time': Song.objects.aggregate(total=Sum('play_count'))['total'] or 0,
            'recent_metrics': DailyPlatformMetric.objects.all()[:7],
            'geo_heatmap': StreamGeoHeatmap.objects.all()[:10],
        }
