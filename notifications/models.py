"""
Real-Time Notification System Models & User Notification Preference Engine.
"""
import uuid
from django.db import models
from django.conf import settings


class NotificationType(models.TextChoices):
    NEW_RELEASE = 'new_release', 'New Release from Followed Artist'
    PLAYLIST_ADD = 'playlist_add', 'Song Added to Collaborative Playlist'
    NEW_FOLLOWER = 'new_follower', 'New Follower on Profile/Artist'
    ROYALTY_PAYOUT = 'royalty_payout', 'Royalty Payout Processed'
    VERIFICATION_UPDATE = 'verification_update', 'Artist Verification Decision'
    SECURITY_ALERT = 'security_alert', 'Account Security Alert'
    SYSTEM_ANNOUNCEMENT = 'system_announcement', 'MusicVerse Platform Announcement'


class Notification(models.Model):
    """
    In-app and push notification record dispatched to users.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NotificationType.choices, default=NotificationType.SYSTEM_ANNOUNCEMENT)
    title = models.CharField(max_length=150)
    message = models.TextField(max_length=500)
    action_url = models.CharField(max_length=255, blank=True, help_text='Link to direct the user to')
    payload = models.JSONField(default=dict, blank=True)
    
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
        ]

    def __str__(self):
        return f"[{self.get_notification_type_display()}] to {self.recipient.username}: {self.title}"


class NotificationPreference(models.Model):
    """
    User-configurable delivery preferences for each notification category.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preferences')
    notify_new_releases = models.BooleanField(default=True)
    notify_playlist_collaborations = models.BooleanField(default=True)
    notify_social_followers = models.BooleanField(default=True)
    notify_royalty_earnings = models.BooleanField(default=True)
    notify_security_events = models.BooleanField(default=True)
    email_digests = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification Preferences for {self.user.username}"
