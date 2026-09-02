"""
Unit & Integration Test Suite for Accounts & Authentication.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, UserPreferences, TwoFactorAuth, UserFollow, UserRole
from accounts.services import AuthenticationService, TwoFactorService, SessionManagementService, ProfileService

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='cosmic_dj',
            email='dj@musicverse.io',
            password='StrongPassword123!@#'
        )
        self.assertEqual(user.username, 'cosmic_dj')
        self.assertEqual(user.email, 'dj@musicverse.io')
        self.assertTrue(user.is_active)
        self.assertEqual(user.role, UserRole.LISTENER)
        self.assertFalse(user.is_premium)
        self.assertTrue(hasattr(user, 'profile'))
        self.assertTrue(hasattr(user, 'preferences'))

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            username='admin_boss',
            email='admin@musicverse.io',
            password='AdminPassword123!@#'
        )
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        self.assertEqual(admin_user.role, UserRole.ADMIN)


class TwoFactorServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='secuser',
            email='sec@musicverse.io',
            password='Password123!@#'
        )

    def test_totp_generation_and_verification(self):
        secret = TwoFactorService.generate_secret()
        self.assertIsNotNone(secret)
        self.assertGreater(len(secret), 16)

        # Generate token and verify immediately
        token = TwoFactorService.get_totp_code(secret)
        self.assertTrue(TwoFactorService.verify_totp(secret, token))

    def test_backup_codes(self):
        plain_codes, hashed_codes = TwoFactorService.generate_backup_codes(4)
        self.assertEqual(len(plain_codes), 4)
        self.assertEqual(len(hashed_codes), 4)

        two_factor = TwoFactorAuth.objects.create(
            user=self.user,
            secret_key='MYSUPERSECRETKEY',
            is_enabled=True,
            backup_codes=hashed_codes
        )

        # Verify and consume first code
        code_to_try = plain_codes[0]
        self.assertTrue(TwoFactorService.verify_and_consume_backup_code(two_factor, code_to_try))
        self.assertEqual(len(two_factor.backup_codes), 3)

        # Trying the same code again fails (single-use)
        self.assertFalse(TwoFactorService.verify_and_consume_backup_code(two_factor, code_to_try))


class ProfileAndFollowServiceTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='u1', email='u1@test.com', password='Pass123!@#')
        self.user2 = User.objects.create_user(username='u2', email='u2@test.com', password='Pass123!@#')

    def test_toggle_follow(self):
        # Follow
        res = ProfileService.toggle_follow_user(self.user1, self.user2)
        self.assertTrue(res)
        self.assertEqual(UserFollow.objects.filter(follower=self.user1, following=self.user2).count(), 1)

        # Unfollow
        res2 = ProfileService.toggle_follow_user(self.user1, self.user2)
        self.assertFalse(res2)
        self.assertEqual(UserFollow.objects.filter(follower=self.user1, following=self.user2).count(), 0)


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='viewtester',
            email='view@musicverse.io',
            password='TestPassword123!@#'
        )

    def test_login_view_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'email': 'view@musicverse.io',
            'password': 'TestPassword123!@#'
        })
        self.assertEqual(response.status_code, 302)

    def test_registration_view(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser101',
            'email': 'newuser101@musicverse.io',
            'password': 'NewUserStrongPass123!',
            'password_confirm': 'NewUserStrongPass123!',
            'account_type': 'listener',
            'terms_accepted': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='newuser101@musicverse.io').exists())
