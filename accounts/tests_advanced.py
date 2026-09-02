"""
Advanced Tests for Social Auth, Tokens, and Onboarding Wizard.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.tokens import account_activation_token, password_reset_token
from accounts.social_auth import OAuthManager, SpotifyOAuthProvider
from music.models import Genre
from artists.models import Artist

User = get_user_model()


class AdvancedAccountTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tokenuser',
            email='token@musicverse.io',
            password='TestPassword123!@#'
        )
        self.genre = Genre.objects.create(name='Cyberwave', color_hex='#00F5D4')
        self.artist = Artist.objects.create(user=self.user, name='Cyber DJ')

    def test_secure_token_generation_and_validation(self):
        token = account_activation_token.make_token(self.user)
        self.assertIsNotNone(token)
        self.assertIn('-', token)

        # Validate token
        is_valid = account_activation_token.check_token(self.user, token)
        self.assertTrue(is_valid)

        # Invalidate with bogus token
        self.assertFalse(account_activation_token.check_token(self.user, 'invalid-token-12345'))

    def test_password_reset_token(self):
        reset_token = password_reset_token.make_token(self.user)
        self.assertTrue(password_reset_token.check_token(self.user, reset_token))

    def test_oauth_manager_resolution(self):
        provider = OAuthManager.get_provider('spotify')
        self.assertIsInstance(provider, SpotifyOAuthProvider)
        auth_url, state = provider.get_authorization_url()
        self.assertIn('https://accounts.spotify.com/authorize', auth_url)
        self.assertIn('client_id=', auth_url)

    def test_onboarding_wizard_step1_to_step3(self):
        client = Client()
        client.force_login(self.user)

        # Step 1
        resp = client.post(reverse('accounts:onboarding') + '?step=1', {'genres': [self.genre.id]})
        self.assertEqual(resp.status_code, 302)

        # Step 2
        resp2 = client.post(reverse('accounts:onboarding') + '?step=2', {'artists': [self.artist.id]})
        self.assertEqual(resp2.status_code, 302)

        # Step 3
        resp3 = client.post(reverse('accounts:onboarding') + '?step=3', {
            'audio_quality': 'lossless',
            'theme': 'neon-cyber',
            'visualizer_mode': 'neon-bars'
        })
        self.assertEqual(resp3.status_code, 302)

        self.user.preferences.refresh_from_db()
        self.assertEqual(self.user.preferences.audio_quality, 'lossless')
        self.assertEqual(self.user.preferences.theme, 'neon-cyber')
