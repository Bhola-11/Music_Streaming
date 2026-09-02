"""
Phase 2 Test Suite — Albums: Discography, Track Listings & Community Reviews.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Album, AlbumTrack, AlbumReview, RecordLabel
from artists.models import Artist
from music.models import Genre, Song

User = get_user_model()


class RecordLabelModelTest(TestCase):
    def test_create_record_label(self):
        label = RecordLabel.objects.create(name='Neon Records', slug='neon-records', country='US')
        self.assertEqual(str(label), 'Neon Records')


class AlbumModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='albartist@mv.io', username='albartist', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='Album Artist', slug='album-artist')
        self.album = Album.objects.create(
            artist=self.artist,
            title='Midnight Transmissions',
            slug='midnight-transmissions',
            album_type='lp',
            is_published=True
        )

    def test_album_created(self):
        self.assertEqual(Album.objects.count(), 1)

    def test_album_str(self):
        self.assertIn('Midnight Transmissions', str(self.album))

    def test_album_type_display(self):
        self.assertIn('lp', self.album.get_album_type_display().lower())


class AlbumTrackTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='trk@mv.io', username='trk', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='Track Artist', slug='track-artist')
        self.genre = Genre.objects.create(name='Jazz', slug='jazz', color_hex='#994422')
        self.album = Album.objects.create(
            artist=self.artist, title='Blue Sessions', slug='blue-sessions',
            album_type='lp', is_published=True
        )
        self.song = Song.objects.create(
            artist=self.artist, title='Midnight Blue', slug='midnight-blue',
            genre=self.genre, duration_seconds=310, is_published=True
        )
        self.track = AlbumTrack.objects.create(
            album=self.album,
            song=self.song,
            track_number=1,
            disc_number=1
        )

    def test_album_track_linked(self):
        self.assertEqual(self.album.album_tracks.count(), 1)

    def test_track_sequencing(self):
        self.assertEqual(self.track.track_number, 1)
        self.assertEqual(self.track.disc_number, 1)


class AlbumDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='albv@mv.io', username='albv', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='View Artist', slug='view-artist')
        self.album = Album.objects.create(
            artist=self.artist, title='Phantom Frequencies', slug='phantom-frequencies',
            album_type='ep', is_published=True
        )

    def test_album_list_returns_200(self):
        url = reverse('albums:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_album_detail_returns_200(self):
        url = reverse('albums:detail', args=[self.album.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_album_detail_contains_title(self):
        url = reverse('albums:detail', args=[self.album.slug])
        response = self.client.get(url)
        self.assertContains(response, 'Phantom Frequencies')


class AlbumReviewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='revr@mv.io', username='revr', password='pass12345')
        self.artist_user = User.objects.create_user(email='revar@mv.io', username='revar', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Review Artist', slug='review-artist')
        self.album = Album.objects.create(
            artist=self.artist, title='Gravity Shift', slug='gravity-shift',
            album_type='lp', is_published=True
        )

    def test_post_album_review(self):
        self.client.login(email='revr@mv.io', password='pass12345')
        url = reverse('albums:add_review', args=[self.album.slug])
        self.client.post(url, {
            'rating': 8,
            'title': 'A masterpiece',
            'body': 'Absolutely breathtaking sonic landscapes.'
        })
        reviews = AlbumReview.objects.filter(album=self.album, user=self.user)
        self.assertEqual(reviews.count(), 1)
        self.assertEqual(reviews.first().rating, 8)
