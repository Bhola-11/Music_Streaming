"""
Phase 3 Test Suite — Notifications: Multi-Channel Dispatch, Preferences & Inbox Management.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
import json

from .models import Notification, NotificationType, NotificationPreference
from .services import NotificationService

User = get_user_model()


class NotificationServiceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='notif_user@mv.io', username='notif_user', password='pass12345')

    def test_send_notification_creates_record(self):
        notif = NotificationService.send_notification(
            recipient=self.user,
            notification_type=NotificationType.NEW_RELEASE,
            title='New Song Out Now',
            message='Your favorite artist just dropped a new master.',
            action_url='/music/songs/'
        )
        self.assertIsNotNone(notif)
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 1)
        self.assertFalse(notif.is_read)

    def test_preference_blocks_notification_when_disabled(self):
        prefs = NotificationPreference.objects.create(user=self.user, notify_new_releases=False)
        notif = NotificationService.send_notification(
            recipient=self.user,
            notification_type=NotificationType.NEW_RELEASE,
            title='Blocked Notification',
            message='This should not be delivered.'
        )
        self.assertIsNone(notif)
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 0)

    def test_mark_as_read(self):
        notif = NotificationService.send_notification(
            recipient=self.user,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            title='Welcome',
            message='Welcome to MusicVerse'
        )
        NotificationService.mark_as_read(notif.id, self.user)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_mark_all_as_read(self):
        NotificationService.send_notification(self.user, NotificationType.SYSTEM_ANNOUNCEMENT, 'Alert 1', 'M1')
        NotificationService.send_notification(self.user, NotificationType.SYSTEM_ANNOUNCEMENT, 'Alert 2', 'M2')
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 2)

        count = NotificationService.mark_all_as_read(self.user)
        self.assertEqual(count, 2)
        self.assertEqual(Notification.objects.filter(recipient=self.user, is_read=False).count(), 0)


class NotificationViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='notif_v@mv.io', username='notif_v', password='pass12345')
        self.client.login(email='notif_v@mv.io', password='pass12345')
        self.notif = NotificationService.send_notification(
            recipient=self.user,
            notification_type=NotificationType.SECURITY_ALERT,
            title='Security Check',
            message='New login from Chrome on Windows'
        )

    def test_notification_list_view(self):
        url = reverse('notifications:list')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Security Check')

    def test_mark_read_api(self):
        url = reverse('notifications:api_mark_read', args=[self.notif.id])
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertTrue(data['success'])

    def test_mark_all_read_api(self):
        url = reverse('notifications:api_mark_all_read')
        res = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        self.assertTrue(data['success'])
