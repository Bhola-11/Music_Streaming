"""
Views for Global Platform Analytics, Artist Deep-Dive Analytics & Real-Time API Metrics.
"""
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.db.models import Sum, Count

from .models import DailyPlatformMetric, StreamGeoHeatmap, SuspiciousActivityFlag
from .services import AnalyticsAggregationService
from artists.models import Artist
from music.models import Song
from player.models import ListeningHistory


class StaffOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_staff or self.request.user.is_superuser)


class PlatformAnalyticsDashboardView(StaffOnlyMixin, TemplateView):
    """
    Administrator command center for stream throughput, bandwidth, server metrics, and fraud detection.
    """
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        overview = AnalyticsAggregationService.get_platform_overview()
        context.update(overview)
        context['suspicious_flags'] = SuspiciousActivityFlag.objects.all()[:15]
        return context


class ArtistAnalyticsDeepDiveView(LoginRequiredMixin, TemplateView):
    """
    Creator Studio deep dive: stream duration completion rates, listener retention, and geographic reach.
    """
    template_name = 'analytics/artist_analytics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        artist = getattr(self.request.user, 'artist_profile', None)
        if not artist:
            return context

        context['artist'] = artist
        context['total_streams'] = Song.objects.filter(artist=artist).aggregate(total=Sum('play_count'))['total'] or 0
        context['tracks'] = Song.objects.filter(artist=artist).order_by('-play_count')[:10]
        context['recent_streams'] = (
            ListeningHistory.objects.filter(song__artist=artist)
            .select_related('song', 'user')
            .order_by('-played_at')[:20]
        )
        return context


class RealtimeMetricsAPIView(StaffOnlyMixin, View):
    """
    Live JSON polling endpoint for administrator HUD meters.
    """
    def get(self, request):
        today_snapshot = AnalyticsAggregationService.generate_today_snapshot()
        return JsonResponse({
            'today_streams': today_snapshot.total_streams,
            'today_listeners': today_snapshot.unique_listeners,
            'bandwidth_gb': float(today_snapshot.bandwidth_served_gb),
            'royalties_usd': float(today_snapshot.royalty_accrued_usd),
        })
