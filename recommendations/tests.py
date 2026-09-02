"""
Phase 4 Test Suite — Algorithmic Recommendations & Daily Mix Generation.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from .models import DailyMix, DailyMixTrack, UserTasteProfile
from .services import RecommendationEngine
from music.models import Song, Genre
from artists.models import Artist

User = get_user_model()


class RecommendationEngineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='rec_u@mv.io', username='rec_u', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='Rec Artist', slug='rec-artist')
        self.genre = Genre.objects.create(name='Cyberpunk', slug='cyberpunk')
        self.song1 = Song.objects.create(artist=self.artist, title='Cyber Track 1', slug='cyber-1', genre=self.genre, is_published=True)
        self.song2 = Song.objects.create(artist=self.artist, title='Cyber Track 2', slug='cyber-2', genre=self.genre, is_published=True)

    def test_generate_daily_mixes(self):
        mixes = RecommendationEngine.generate_daily_mixes_for_user(self.user)
        self.assertGreaterEqual(len(mixes), 1)
        self.assertEqual(DailyMix.objects.filter(user=self.user).count(), len(mixes))

    def test_similar_songs(self):
        similars = RecommendationEngine.get_similar_songs(self.song1)
        self.assertIn(self.song2, similars)


class RecommendationViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='rec_v@mv.io', username='rec_v', password='pass12345')
        self.client.login(email='rec_v@mv.io', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='View Artist', slug='view-artist')
        self.genre = Genre.objects.create(name='Chillhop', slug='chillhop')
        self.song = Song.objects.create(artist=self.artist, title='Chill Song', slug='chill-song', genre=self.genre, is_published=True)

    def test_feed_view(self):
        url = reverse('recommendations:feed')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)

    def test_similar_tracks_api(self):
        url = reverse('recommendations:api_similar', args=[self.song.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertTrue(data['success'])
