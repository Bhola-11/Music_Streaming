"""
Phase 4 Test Suite — Discovery, Global Multi-Entity Search & Official Charts.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import FeaturedBanner, MusicChart, ChartEntry, SearchQueryLog
from music.models import Song, Genre
from artists.models import Artist
from albums.models import Album
from playlists.models import Playlist

User = get_user_model()


class DiscoveryViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='disc_user@mv.io', username='disc_user', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='Discovery Artist', slug='discovery-artist')
        self.genre = Genre.objects.create(name='Synth', slug='synth')
        self.song = Song.objects.create(artist=self.artist, title='Discovery Beat', slug='discovery-beat', genre=self.genre, is_published=True)
        self.chart = MusicChart.objects.create(title='Top 50 Global', slug='top-50-global')
        ChartEntry.objects.create(chart=self.chart, song=self.song, rank=1)

    def test_discovery_hub_view(self):
        url = reverse('discovery:hub')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_global_search_finds_song_and_logs(self):
        url = reverse('discovery:search') + '?q=Discovery'
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Discovery Beat')
        self.assertEqual(SearchQueryLog.objects.count(), 1)

    def test_charts_list_view(self):
        url = reverse('discovery:charts')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Top 50 Global')

    def test_chart_detail_view(self):
        url = reverse('discovery:chart_detail', args=[self.chart.slug])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Discovery Beat')
