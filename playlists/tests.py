"""
Phase 3 Test Suite — Playlists: Creation, Track Ordering, Collaborative Curation & Social Bookmarking.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from .models import Playlist, PlaylistTrack, PlaylistCollaborator, PlaylistFollower, PlaylistPrivacy, CollaboratorRole
from music.models import Song, Genre
from artists.models import Artist

User = get_user_model()


class PlaylistModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='pl_owner@mv.io', username='pl_owner', password='pass12345')
        self.playlist = Playlist.objects.create(
            owner=self.user,
            title='Synthwave Essentials',
            slug='synthwave-essentials',
            description='Ultimate retro futuristic beats',
            privacy=PlaylistPrivacy.PUBLIC
        )

    def test_playlist_created(self):
        self.assertEqual(Playlist.objects.count(), 1)

    def test_playlist_str(self):
        self.assertIn('Synthwave Essentials', str(self.playlist))

    def test_cover_art_url_fallback(self):
        url = self.playlist.cover_art_url
        self.assertIsNotNone(url)


class PlaylistTrackOrderingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='curator@mv.io', username='curator', password='pass12345')
        self.artist_user = User.objects.create_user(email='art_pl@mv.io', username='art_pl', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Vapor Artist', slug='vapor-artist')
        self.genre = Genre.objects.create(name='Vaporwave', slug='vaporwave')

        self.playlist = Playlist.objects.create(owner=self.user, title='Vapor Chill', slug='vapor-chill')
        self.song1 = Song.objects.create(artist=self.artist, title='Track One', slug='track-one', genre=self.genre, duration_seconds=120)
        self.song2 = Song.objects.create(artist=self.artist, title='Track Two', slug='track-two', genre=self.genre, duration_seconds=180)

        self.pt1 = PlaylistTrack.objects.create(playlist=self.playlist, song=self.song1, position=1)
        self.pt2 = PlaylistTrack.objects.create(playlist=self.playlist, song=self.song2, position=2)

    def test_tracklist_sequencing(self):
        tracks = self.playlist.playlist_tracks.all()
        self.assertEqual(tracks.count(), 2)
        self.assertEqual(tracks[0].song, self.song1)
        self.assertEqual(tracks[1].song, self.song2)

    def test_total_duration_calculation(self):
        self.assertEqual(self.playlist.total_duration_seconds, 300)
        self.assertIn('5 min', self.playlist.formatted_total_duration)


class PlaylistCollaboratorTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner1@mv.io', username='owner1', password='pass12345')
        self.friend = User.objects.create_user(email='friend1@mv.io', username='friend1', password='pass12345')
        self.playlist = Playlist.objects.create(owner=self.owner, title='Shared Vibes', slug='shared-vibes', is_collaborative=True)

    def test_add_collaborator(self):
        collab = PlaylistCollaborator.objects.create(
            playlist=self.playlist,
            user=self.friend,
            role=CollaboratorRole.EDITOR
        )
        self.assertEqual(collab.role, CollaboratorRole.EDITOR)
        self.assertEqual(self.playlist.collaborators.count(), 1)


class PlaylistViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='viewer_pl@mv.io', username='viewer_pl', password='pass12345')
        self.artist_user = User.objects.create_user(email='art_plv@mv.io', username='art_plv', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Art PLV', slug='art-plv')
        self.genre = Genre.objects.create(name='Lo-Fi', slug='lo-fi')
        self.song = Song.objects.create(artist=self.artist, title='Study Beats', slug='study-beats', genre=self.genre)
        self.playlist = Playlist.objects.create(owner=self.user, title='Study Session', slug='study-session')

    def test_playlist_list_view(self):
        url = reverse('playlists:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_playlist_detail_view(self):
        url = reverse('playlists:detail', args=[self.playlist.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Study Session')

    def test_add_track_api(self):
        self.client.login(email='viewer_pl@mv.io', password='pass12345')
        url = reverse('playlists:api_add_track', args=[self.playlist.id])
        response = self.client.post(url, {'song_id': str(self.song.id)})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(PlaylistTrack.objects.filter(playlist=self.playlist, song=self.song).count(), 1)

    def test_remove_track_api(self):
        self.client.login(email='viewer_pl@mv.io', password='pass12345')
        PlaylistTrack.objects.create(playlist=self.playlist, song=self.song, position=1)

        url = reverse('playlists:api_remove_track', args=[self.playlist.id, self.song.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PlaylistTrack.objects.filter(playlist=self.playlist).count(), 0)

    def test_reorder_tracks_api(self):
        self.client.login(email='viewer_pl@mv.io', password='pass12345')
        song2 = Song.objects.create(artist=self.artist, title='Beat 2', slug='beat-2', genre=self.genre)
        pt1 = PlaylistTrack.objects.create(playlist=self.playlist, song=self.song, position=1)
        pt2 = PlaylistTrack.objects.create(playlist=self.playlist, song=song2, position=2)

        url = reverse('playlists:api_reorder_tracks', args=[self.playlist.id])
        payload = json.dumps({'order': [str(song2.id), str(self.song.id)]})
        response = self.client.post(url, data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        pt1.refresh_from_db()
        pt2.refresh_from_db()
        self.assertEqual(pt2.position, 1)
        self.assertEqual(pt1.position, 2)
