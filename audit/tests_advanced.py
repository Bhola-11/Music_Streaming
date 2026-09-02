"""
Advanced Tests for Security Anomaly Detection & GDPR Compliance.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from audit.models import SecurityEvent, ActionSeverity
from audit.anomaly_detector import SecurityAnomalyDetector
from audit.compliance import ComplianceManager

User = get_user_model()


class AnomalyAndComplianceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='gdpruser',
            email='gdpr@musicverse.io',
            password='TestPassword123!@#'
        )

    def test_ip_brute_force_detection(self):
        # Trigger simulated failed logins
        for _ in range(12):
            SecurityEvent.objects.create(
                event_type='failed_login',
                severity=ActionSeverity.MEDIUM,
                source_ip='198.51.100.25'
            )

        is_blocked = SecurityAnomalyDetector.scan_ip_reputation('198.51.100.25', threshold_fails=10)
        self.assertTrue(is_blocked)

    def test_streaming_farm_anomaly(self):
        anomaly_detected = SecurityAnomalyDetector.detect_streaming_farm_anomaly(self.user, streams_in_10min=200)
        self.assertTrue(anomaly_detected)

    def test_gdpr_data_export(self):
        export_data = ComplianceManager.generate_user_data_export(self.user)
        self.assertEqual(export_data['metadata']['email'], 'gdpr@musicverse.io')
        self.assertIn('profile', export_data)
        self.assertIn('preferences', export_data)

    def test_gdpr_anonymization(self):
        success = ComplianceManager.anonymize_user_account(self.user)
        self.assertTrue(success)

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertIn('anonymized.musicverse.io', self.user.email)
