"""
Tests for the Audit & Security Trail system.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from audit.models import AuditLog, SecurityEvent, ActionCategory, ActionSeverity
from audit.services import AuditService
from audit.middleware import AuditLoggingMiddleware

User = get_user_model()


class AuditServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='audittester',
            email='audit@musicverse.io',
            password='Password123!@#',
            role='listener'
        )

    def test_log_action_creation(self):
        log = AuditService.log_action(
            action_type='song.stream.start',
            category=ActionCategory.MUSIC_CATALOG,
            severity=ActionSeverity.INFO,
            description='User started streaming a track',
            user=self.user,
            target_model='Song',
            target_object_id='100',
            ip_address='192.168.1.50',
            request_path='/music/stream/100/',
            metadata={'bitrate': 320, 'format': 'mp3'}
        )

        self.assertIsNotNone(log.id)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.actor_email, 'audit@musicverse.io')
        self.assertEqual(log.category, ActionCategory.MUSIC_CATALOG)
        self.assertEqual(log.action_type, 'song.stream.start')
        self.assertIsNotNone(log.signature)

    def test_log_security_event(self):
        sec_event = AuditService.log_security_event(
            event_type='brute_force_detected',
            severity=ActionSeverity.CRITICAL,
            source_ip='10.0.0.99',
            details={'attempts': 15}
        )

        self.assertIsNotNone(sec_event.id)
        self.assertEqual(sec_event.severity, ActionSeverity.CRITICAL)
        self.assertEqual(sec_event.source_ip, '10.0.0.99')
        self.assertFalse(sec_event.is_resolved)

    def test_security_summary_aggregation(self):
        AuditService.log_action(action_type='test.action.1', user=self.user)
        AuditService.log_action(action_type='test.action.2', user=self.user)
        AuditService.log_security_event(event_type='failed_login', user=self.user)

        summary = AuditService.get_security_summary()
        self.assertGreaterEqual(summary['total_logs'], 2)
        self.assertGreaterEqual(summary['unresolved_security_events'], 1)


class AuditMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AuditLoggingMiddleware(get_response=lambda r: None)
        self.user = User.objects.create_user(
            username='middleuser',
            email='middle@musicverse.io',
            password='Password123!@#',
        )

    def test_auth_path_post_triggers_audit(self):
        request = self.factory.post('/accounts/login/', {'email': 'middle@musicverse.io'})
        request.user = self.user
        
        from django.http import HttpResponse
        response = HttpResponse(status=200)

        self.middleware.process_response(request, response)

        log = AuditLog.objects.filter(action_type='auth.login_attempt').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.request_path, '/accounts/login/')
