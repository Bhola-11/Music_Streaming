"""
Phase 5 Test Suite — Content Moderation, Copyright DMCA Claims & Quarantine Automation.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import ModerationReport, TakedownRequest, ModerationStatus, ReportReason
from .services import ModerationService
from music.models import Song, Genre
from artists.models import Artist

User = get_user_model()


class ModerationWorkflowTest(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_superuser(email='mod@mv.io', username='moderator', password='pass12345')
        self.artist_user = User.objects.create_user(email='target_art@mv.io', username='target_art', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Flagged Artist', slug='flagged-artist')
        self.genre = Genre.objects.create(name='Drill', slug='drill')
        self.song = Song.objects.create(artist=self.artist, title='Unreleased Demo', slug='unreleased-demo', genre=self.genre, is_published=True)

        self.report = ModerationReport.objects.create(
            reason=ReportReason.AUDIO_LEAK,
            song=self.song,
            description='Unlicensed leak of studio session recording'
        )

    def test_takedown_service_unpublishes_song(self):
        self.assertTrue(self.song.is_published)
        ModerationService.execute_takedown(
            report=self.report,
            moderator_user=self.staff_user,
            reason_notes='Confirmed leaked master from unreleased stems'
        )
        self.report.refresh_from_db()
        self.song.refresh_from_db()

        self.assertEqual(self.report.status, ModerationStatus.RESOLVED_REMOVED)
        self.assertFalse(self.song.is_published)

    def test_dismiss_report_service(self):
        ModerationService.dismiss_report(
            report=self.report,
            moderator_user=self.staff_user,
            reason_notes='Legitimate official release'
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ModerationStatus.RESOLVED_DISMISSED)


class ModerationViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_superuser(email='staff@mv.io', username='staff', password='pass12345')
        self.regular = User.objects.create_user(email='reg@mv.io', username='regular', password='pass12345')
        self.artist = Artist.objects.create(user=self.regular, name='Band', slug='band')
        self.genre = Genre.objects.create(name='Metal', slug='metal')
        self.song = Song.objects.create(artist=self.artist, title='Heavy Riff', slug='heavy-riff', genre=self.genre)

    def test_queue_view_requires_staff(self):
        url = reverse('moderation:queue')
        # Anonymous
        res1 = self.client.get(url)
        self.assertEqual(res1.status_code, 302)

        # Regular user
        self.client.login(email='reg@mv.io', password='pass12345')
        res2 = self.client.get(url)
        self.assertEqual(res2.status_code, 403)

        # Staff user
        self.client.login(email='staff@mv.io', password='pass12345')
        res3 = self.client.get(url)
        self.assertEqual(res3.status_code, 200)

    def test_file_report_view(self):
        self.client.login(email='reg@mv.io', password='pass12345')
        url = reverse('moderation:file_report', args=[self.song.id])
        res = self.client.post(url, {
            'reason': ReportReason.EXPLICIT_UNMARKED,
            'description': 'Contains explicit language not flagged in metadata'
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(ModerationReport.objects.filter(song=self.song).count(), 1)
