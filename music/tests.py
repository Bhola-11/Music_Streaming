"""
Phase 2 Test Suite — Music Catalog: Songs, Streaming, Genres, Lyrics, and Audio Metadata.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import json

from .models import Genre, Mood, Song, Lyrics, TrackComment, TrackRating
from .audio_processor import AudioMetadataExtractor, WaveformPeakGenerator
from .range_streamer import get_range_response
from artists.models import Artist

User = get_user_model()


class GenreMoodModelTest(TestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name='Electronic', slug='electronic', color_hex='#00C3FF')
        self.mood = Mood.objects.create(name='Energetic', slug='energetic', icon='⚡')

    def test_genre_str(self):
        self.assertEqual(str(self.genre), 'Electronic')

    def test_mood_str(self):
        self.assertIn('Energetic', str(self.mood))

    def test_genre_slugified(self):
        self.assertEqual(self.genre.slug, 'electronic')


class SongModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='artist@mv.io', username='artistuser', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='Test Artist', slug='test-artist')
        self.genre = Genre.objects.create(name='Synthwave', slug='synthwave', color_hex='#FF2D7B')
        self.song = Song.objects.create(
            artist=self.artist,
            title='Neon Drive',
            slug='neon-drive',
            genre=self.genre,
            duration_seconds=214,
            bitrate_kbps=320,
            sample_rate_hz=44100,
            is_published=True,
        )

    def test_song_created(self):
        self.assertEqual(Song.objects.count(), 1)

    def test_formatted_duration(self):
        duration = self.song.formatted_duration
        self.assertIn(':', duration)
        self.assertEqual(duration, '3:34')

    def test_play_count_default_zero(self):
        self.assertEqual(self.song.play_count, 0)

    def test_song_str(self):
        self.assertIn('Neon Drive', str(self.song))


class LyricsModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='lyricist@mv.io', username='lyricist', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='Lyricist', slug='lyricist')
        self.genre = Genre.objects.create(name='Pop', slug='pop', color_hex='#FF9900')
        self.song = Song.objects.create(
            artist=self.artist,
            title='Summer Vibes',
            slug='summer-vibes',
            genre=self.genre,
            is_published=True
        )
        self.lyrics = Lyrics.objects.create(
            song=self.song,
            plain_lyrics="Verse one\nVerse two",
            writer_credit='The Artist',
            is_synced=False
        )

    def test_lyrics_attached_to_song(self):
        self.assertEqual(self.song.lyrics.plain_lyrics, "Verse one\nVerse two")

    def test_lyrics_str(self):
        self.assertIn('Summer Vibes', str(self.lyrics))


class TrackRatingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='fan@mv.io', username='fanuser', password='pass12345')
        self.artist_user = User.objects.create_user(email='art2@mv.io', username='art2', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Deep Tones', slug='deep-tones')
        self.genre = Genre.objects.create(name='Ambient', slug='ambient', color_hex='#9966FF')
        self.song = Song.objects.create(
            artist=self.artist, title='Cosmic Flow', slug='cosmic-flow',
            genre=self.genre, is_published=True
        )

    def test_create_rating(self):
        rating = TrackRating.objects.create(user=self.user, song=self.song, stars=4)
        self.assertEqual(rating.stars, 4)

    def test_upsert_rating(self):
        TrackRating.objects.create(user=self.user, song=self.song, stars=3)
        TrackRating.objects.update_or_create(
            user=self.user, song=self.song, defaults={'stars': 5}
        )
        self.assertEqual(TrackRating.objects.get(user=self.user, song=self.song).stars, 5)


class WaveformPeakGeneratorTest(TestCase):
    def test_waveform_returns_list_of_peaks(self):
        dummy = SimpleUploadedFile("test.mp3", b"\xff\xe3" + b'\x00' * 500, content_type="audio/mpeg")
        result = WaveformPeakGenerator.generate_waveform(dummy, points_count=60)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 60)
        for v in result:
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)


class AudioMetadataExtractorTest(TestCase):
    def test_returns_dict_with_required_keys(self):
        # Using a dummy file, fallback metadata expected
        dummy = SimpleUploadedFile("test.mp3", b"\xff\xe3" + b'\x00' * 100, content_type="audio/mpeg")
        meta = AudioMetadataExtractor.extract_metadata(dummy)
        self.assertIsInstance(meta, dict)
        self.assertIn('duration_seconds', meta)
        self.assertIn('bitrate_kbps', meta)


class SongDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='viewer@mv.io', username='viewer', password='pass12345')
        self.artist_user = User.objects.create_user(email='artv@mv.io', username='artv', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Nightwave', slug='nightwave')
        self.genre = Genre.objects.create(name='Dark Ambient', slug='dark-ambient', color_hex='#220033')
        self.song = Song.objects.create(
            artist=self.artist, title='Dark Matter', slug='dark-matter',
            genre=self.genre, is_published=True
        )

    def test_song_detail_returns_200(self):
        url = reverse('music:song_detail', args=[self.song.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_song_detail_contains_title(self):
        url = reverse('music:song_detail', args=[self.song.id])
        response = self.client.get(url)
        self.assertContains(response, 'Dark Matter')

    def test_song_list_view_returns_200(self):
        url = reverse('music:song_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_lyrics_api_no_lyrics_returns_empty(self):
        url = reverse('music:lyrics_api', args=[self.song.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['has_lyrics'])


class RateSongViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='rater@mv.io', username='rater', password='pass12345')
        self.artist_user = User.objects.create_user(email='artr@mv.io', username='artr', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Rater Artist', slug='rater-artist')
        self.genre = Genre.objects.create(name='Hip-Hop', slug='hip-hop', color_hex='#FF8800')
        self.song = Song.objects.create(
            artist=self.artist, title='Flow State', slug='flow-state',
            genre=self.genre, is_published=True
        )

    def test_rate_song_creates_rating(self):
        self.client.login(email='rater@mv.io', password='pass12345')
        url = reverse('music:rate_song', args=[self.song.id])
        self.client.post(url, {'stars': 5})
        rating = TrackRating.objects.filter(user=self.user, song=self.song).first()
        self.assertIsNotNone(rating)
        self.assertEqual(rating.stars, 5)
