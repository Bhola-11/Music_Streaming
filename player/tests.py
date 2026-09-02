"""
Phase 3 Test Suite — Player: Playback Queues, Listening History, Favorites Library & Dynamic Radio.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from .models import PlaybackQueue, QueueItem, ListeningHistory, FavoriteTrack, PlaybackSession, RadioStation
from music.models import Song, Genre
from artists.models import Artist

User = get_user_model()


class FavoriteTrackTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='fav_user@mv.io', username='fav_user', password='pass12345')
        self.artist_user = User.objects.create_user(email='art_f@mv.io', username='art_f', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Electro Pulse', slug='electro-pulse')
        self.genre = Genre.objects.create(name='Electro', slug='electro')
        self.song = Song.objects.create(artist=self.artist, title='Voltage', slug='voltage', genre=self.genre)

    def test_toggle_favorite_api(self):
        client = Client()
        client.login(email='fav_user@mv.io', password='pass12345')
        url = reverse('player:api_toggle_favorite', args=[self.song.id])

        # 1. Like
        res1 = client.post(url)
        self.assertEqual(res1.status_code, 200)
        data1 = json.loads(res1.content)
        self.assertTrue(data1['is_favorite'])
        self.assertEqual(FavoriteTrack.objects.filter(user=self.user, song=self.song).count(), 1)

        # 2. Unlike
        res2 = client.post(url)
        data2 = json.loads(res2.content)
        self.assertFalse(data2['is_favorite'])
        self.assertEqual(FavoriteTrack.objects.filter(user=self.user, song=self.song).count(), 0)


class PlaybackQueueTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='q_user@mv.io', username='q_user', password='pass12345')
        self.artist_user = User.objects.create_user(email='art_q@mv.io', username='art_q', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Queue Band', slug='queue-band')
        self.genre = Genre.objects.create(name='Rock', slug='rock')
        self.song = Song.objects.create(artist=self.artist, title='Riff 1', slug='riff-1', genre=self.genre)

    def test_queue_add_and_list(self):
        self.client.login(email='q_user@mv.io', password='pass12345')
        add_url = reverse('player:api_queue_add', args=[self.song.id])
        res = self.client.post(add_url)
        self.assertEqual(res.status_code, 200)

        list_url = reverse('player:api_get_queue')
        res_list = self.client.get(list_url)
        data = json.loads(res_list.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['queue']), 1)
        self.assertEqual(data['queue'][0]['title'], 'Riff 1')


class ListeningHistoryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='hist_user@mv.io', username='hist_user', password='pass12345')
        self.artist_user = User.objects.create_user(email='art_h@mv.io', username='art_h', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Bassline', slug='bassline')
        self.genre = Genre.objects.create(name='House', slug='house')
        self.song = Song.objects.create(artist=self.artist, title='Deep Bass', slug='deep-bass', genre=self.genre)

    def test_record_history_api(self):
        self.client.login(email='hist_user@mv.io', password='pass12345')
        url = reverse('player:api_record_history', args=[self.song.id])
        payload = json.dumps({
            'seconds_played': 140,
            'completion_pct': 92.5,
            'was_skipped': False
        })
        res = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(ListeningHistory.objects.filter(user=self.user, song=self.song).count(), 1)


class RadioStationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.artist_user = User.objects.create_user(email='art_r@mv.io', username='art_r', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Solar Sound', slug='solar-sound')
        self.genre = Genre.objects.create(name='Trance', slug='trance')
        self.song1 = Song.objects.create(artist=self.artist, title='Trance Anthem', slug='trance-anthem', genre=self.genre, is_published=True)
        self.song2 = Song.objects.create(artist=self.artist, title='Sunburst', slug='sunburst', genre=self.genre, is_published=True)

    def test_start_radio_api(self):
        url = reverse('player:api_start_radio', args=[self.song1.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertTrue(data['success'])
        self.assertGreaterEqual(len(data['radio_tracks']), 1)
