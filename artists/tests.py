"""
Phase 2 Test Suite — Artists: Profiles, Verification Workflow, Royalties, and Social Graph.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal
from unittest.mock import patch
from datetime import date

from .models import Artist, ArtistVerificationRequest, ArtistFollower, RoyaltyStatement, VerificationStatus
from .services import RoyaltyCalculatorService, VerificationService

User = get_user_model()


class ArtistModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='am@mv.io', username='am', password='pass12345')
        self.artist = Artist.objects.create(
            user=self.user,
            name='Digital Noir',
            slug='digital-noir',
            country_of_origin='Germany'
        )

    def test_artist_created(self):
        self.assertEqual(Artist.objects.count(), 1)

    def test_artist_str(self):
        self.assertIn('Digital Noir', str(self.artist))

    def test_artist_defaults(self):
        self.assertEqual(self.artist.verification_status, VerificationStatus.UNVERIFIED)
        self.assertEqual(self.artist.monthly_listeners, 0)
        self.assertEqual(self.artist.total_streams, 0)


class ArtistFollowerTest(TestCase):
    def setUp(self):
        self.fan = User.objects.create_user(email='fan2@mv.io', username='fan2', password='pass12345')
        self.artist_user = User.objects.create_user(email='art3@mv.io', username='art3', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Void Pulse', slug='void-pulse')

    def test_follow_artist(self):
        ArtistFollower.objects.create(user=self.fan, artist=self.artist)
        self.assertEqual(ArtistFollower.objects.filter(artist=self.artist).count(), 1)

    def test_unfollow_artist(self):
        af = ArtistFollower.objects.create(user=self.fan, artist=self.artist)
        af.delete()
        self.assertEqual(ArtistFollower.objects.filter(artist=self.artist).count(), 0)


class ArtistVerificationTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(email='admin@mv.io', username='admin', password='pass12345')
        self.artist_user = User.objects.create_user(email='vrf@mv.io', username='vrf', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Solar Haze', slug='solar-haze')
        self.request_obj = ArtistVerificationRequest.objects.create(
            artist=self.artist,
            legal_name='Solar Haze Collective LLC',
            social_proof_links='https://spotify.com/solarhaze',
            status=VerificationStatus.PENDING
        )

    def test_approve_verification(self):
        VerificationService.approve_verification(self.request_obj, reviewer_user=self.admin_user)
        self.request_obj.refresh_from_db()
        self.artist.refresh_from_db()
        self.assertEqual(self.request_obj.status, VerificationStatus.VERIFIED)
        self.assertEqual(self.artist.verification_status, VerificationStatus.VERIFIED)

    def test_reject_verification(self):
        VerificationService.reject_verification(
            self.request_obj, reviewer_user=self.admin_user, reason='Insufficient documentation'
        )
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, VerificationStatus.REJECTED)
        self.assertEqual(self.request_obj.rejection_reason, 'Insufficient documentation')


class ArtistProfileViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='apv@mv.io', username='apv', password='pass12345')
        self.artist = Artist.objects.create(user=self.user, name='Aurora Beats', slug='aurora-beats')

    def test_artist_list_returns_200(self):
        url = reverse('artists:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_artist_detail_returns_200(self):
        url = reverse('artists:detail', args=[self.artist.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_artist_detail_contains_name(self):
        url = reverse('artists:detail', args=[self.artist.slug])
        response = self.client.get(url)
        self.assertContains(response, 'Aurora Beats')

    def test_dashboard_requires_login(self):
        url = reverse('artists:dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirected to login

    def test_dashboard_authenticated(self):
        self.client.login(email='apv@mv.io', password='pass12345')
        url = reverse('artists:dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class ToggleFollowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.fan = User.objects.create_user(email='tfan@mv.io', username='tfan', password='pass12345')
        self.artist_user = User.objects.create_user(email='tart@mv.io', username='tart', password='pass12345')
        self.artist = Artist.objects.create(user=self.artist_user, name='Pulsed Bass', slug='pulsed-bass')

    def test_toggle_follow(self):
        self.client.login(email='tfan@mv.io', password='pass12345')
        url = reverse('artists:toggle_follow', args=[self.artist.slug])
        # Follow
        self.client.post(url)
        self.assertEqual(ArtistFollower.objects.filter(user=self.fan, artist=self.artist).count(), 1)
        # Unfollow
        self.client.post(url)
        self.assertEqual(ArtistFollower.objects.filter(user=self.fan, artist=self.artist).count(), 0)
