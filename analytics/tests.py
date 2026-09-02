"""
Phase 5 Test Suite — Global Platform Analytics, Stream Farm Detection & Real-Time Telemetry.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

from .models import DailyPlatformMetric, StreamGeoHeatmap, SuspiciousActivityFlag
from .services import AnalyticsAggregationService
from music.models import Song, Genre
from artists.models import Artist
from player.models import ListeningHistory

User = get_user_model()


class AnalyticsAggregationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='analytics_u@mv.io', username='analytics_u', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='Data Artist', slug='data-artist')
        self.genre = Genre.objects.create(name='Techno', slug='techno')
        self.song = Song.objects.create(artist=self.artist, title='Beat Stream', slug='beat-stream', genre=self.genre)

        # Record a listening event
        ListeningHistory.objects.create(
            user=self.user,
            song=self.song,
            seconds_played=180,
            completion_percentage=100.0,
            played_at=timezone.now()
        )

    def test_daily_snapshot_rollup(self):
        snapshot = AnalyticsAggregationService.generate_today_snapshot()
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.total_streams, 1)
        self.assertEqual(snapshot.unique_listeners, 1)

    def test_overview_service(self):
        overview = AnalyticsAggregationService.get_platform_overview()
        self.assertIn('total_users', overview)
        self.assertIn('total_songs', overview)
        self.assertIn('total_artists', overview)


class AnalyticsViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_superuser(email='staff_a@mv.io', username='staff_a', password='pass12345')
        self.client.login(email='staff_a@mv.io', password='pass12345')

    def test_analytics_dashboard_view(self):
        url = reverse('analytics:dashboard')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Global Platform Intelligence')

    def test_realtime_metrics_api(self):
        url = reverse('analytics:realtime_api')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertIn('today_streams', data)
        self.assertIn('bandwidth_gb', data)
