"""
Audit & Security Trail Models.
Provides tamper-resistant logging for authentication events, role changes,
financial operations, track deletions, takedown requests, and administrator actions.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class ActionCategory(models.TextChoices):
    AUTHENTICATION = 'AUTH', 'Authentication & Access'
    USER_MANAGEMENT = 'USER', 'User Management'
    ARTIST_ACTION = 'ARTIST', 'Artist Actions'
    MUSIC_CATALOG = 'MUSIC', 'Music & Media Catalog'
    FINANCIAL = 'FINANCE', 'Subscription & Financial'
    MODERATION = 'MODERATION', 'Moderation & Takedowns'
    SYSTEM_CONFIG = 'SYSTEM', 'System Configuration'
    SECURITY_ALERT = 'SECURITY', 'Security Anomaly'


class ActionSeverity(models.TextChoices):
    INFO = 'INFO', 'Informational'
    LOW = 'LOW', 'Low Risk'
    MEDIUM = 'MEDIUM', 'Medium Risk'
    HIGH = 'HIGH', 'High Severity'
    CRITICAL = 'CRITICAL', 'Critical Alert'


class AuditLog(models.Model):
    """
    Core immutable record of significant user, artist, and administrative operations.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='User who initiated the action, or null for system events.'
    )
    actor_email = models.EmailField(blank=True, null=True, help_text='Snapshot of email at time of action.')
    actor_role = models.CharField(max_length=50, blank=True, default='anonymous')
    
    category = models.CharField(
        max_length=20,
        choices=ActionCategory.choices,
        default=ActionCategory.AUTHENTICATION,
        db_index=True
    )
    severity = models.CharField(
        max_length=20,
        choices=ActionSeverity.choices,
        default=ActionSeverity.INFO,
        db_index=True
    )
    action_type = models.CharField(
        max_length=120,
        db_index=True,
        help_text='e.g., user.login, song.upload, subscription.canceled, admin.ban'
    )
    description = models.TextField(help_text='Human-readable description of what transpired.')
    
    # Target entity metadata
    target_model = models.CharField(max_length=100, blank=True, null=True, help_text='e.g., Song, User, Invoice')
    target_object_id = models.CharField(max_length=255, blank=True, null=True)
    target_repr = models.CharField(max_length=255, blank=True, null=True, help_text='String representation of target')
    
    # Network and Client Telemetry
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True, null=True)
    request_method = models.CharField(max_length=10, blank=True, default='GET')
    request_path = models.CharField(max_length=500, blank=True, default='')
    status_code = models.PositiveIntegerField(null=True, blank=True)
    
    # State Diffs and Payload Snapshots
    pre_change_state = models.JSONField(blank=True, null=True, help_text='JSON diff before modification')
    post_change_state = models.JSONField(blank=True, null=True, help_text='JSON diff after modification')
    metadata = models.JSONField(blank=True, default=dict, help_text='Arbitrary extra context and parameters')
    
    # Integrity Verification Hash
    signature = models.CharField(max_length=128, blank=True, null=True, help_text='Cryptographic digest of the entry')
    
    timestamp = models.DateTimeField(default=timezone.now, db_index=True, editable=False)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['category', 'severity']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'

    def __str__(self):
        actor = self.actor_email or (self.user.email if self.user else 'System')
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] ({self.severity}) {actor} -> {self.action_type}"


class SecurityEvent(models.Model):
    """
    Dedicated model for suspicious security triggers: brute force login attempts,
    suspicious IP geographic shifts, token reuse, rate-limit breeches, and permission bypasses.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_events'
    )
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text='e.g., failed_login, token_expired, rate_limit_exceeded, sql_injection_pattern'
    )
    severity = models.CharField(
        max_length=20,
        choices=ActionSeverity.choices,
        default=ActionSeverity.HIGH,
        db_index=True
    )
    source_ip = models.GenericIPAddressField(db_index=True)
    user_agent = models.TextField(blank=True, default='')
    country_code = models.CharField(max_length=10, blank=True, default='XX')
    city = models.CharField(max_length=100, blank=True, default='Unknown')
    details = models.JSONField(default=dict)
    
    is_resolved = models.BooleanField(default=False, db_index=True)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_events'
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'

    def __str__(self):
        return f"Security Alert: {self.event_type} from {self.source_ip} [{self.severity}]"


class APIRequestLog(models.Model):
    """
    Telemetry log for high-frequency internal and external API calls and audio stream tokens.
    """
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    endpoint = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=10)
    status_code = models.PositiveIntegerField()
    execution_time_ms = models.FloatField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'API Request Log'
        verbose_name_plural = 'API Request Logs'


class AdminActionLog(models.Model):
    """
    Tracks privileged staff actions: artist verification, copyright takedowns, refund approvals.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='privileged_admin_actions'
    )
    action = models.CharField(max_length=150)
    target_entity = models.CharField(max_length=150)
    justification_reason = models.TextField(help_text='Mandatory reasoning provided by the admin.')
    changes_applied = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Privileged Action'
        verbose_name_plural = 'Admin Privileged Actions'


class AuditRetentionPolicy(models.Model):
    """
    Configurable data retention rules for compliance (e.g. GDPR, CCPA, SOC2).
    """
    category = models.CharField(max_length=20, choices=ActionCategory.choices, unique=True)
    retention_days = models.PositiveIntegerField(default=365)
    auto_archive = models.BooleanField(default=True)
    last_cleaned_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Retention: {self.get_category_display()} ({self.retention_days} days)"
