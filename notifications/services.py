"""
Notification Service: Multi-Channel Dispatch & Event Broadcaster.
"""
from typing import Optional, Dict
from django.utils import timezone
from .models import Notification, NotificationType, NotificationPreference


class NotificationService:
    """
    Centralized dispatcher for creating and broadcasting user notifications.
    """

    @classmethod
    def send_notification(
        cls,
        recipient,
        notification_type: str,
        title: str,
        message: str,
        action_url: str = '',
        payload: Optional[Dict] = None
    ) -> Optional[Notification]:
        """
        Creates an in-app notification if the recipient's preference allows it.
        """
        # Verify user preferences
        prefs, _ = NotificationPreference.objects.get_or_create(user=recipient)

        if notification_type == NotificationType.NEW_RELEASE and not prefs.notify_new_releases:
            return None
        if notification_type == NotificationType.PLAYLIST_ADD and not prefs.notify_playlist_collaborations:
            return None
        if notification_type == NotificationType.NEW_FOLLOWER and not prefs.notify_social_followers:
            return None
        if notification_type == NotificationType.ROYALTY_PAYOUT and not prefs.notify_royalty_earnings:
            return None
        if notification_type == NotificationType.SECURITY_ALERT and not prefs.notify_security_events:
            return None

        notif = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            action_url=action_url,
            payload=payload or {}
        )
        return notif

    @classmethod
    def mark_as_read(cls, notification_id, user) -> bool:
        """Marks a specific notification as read."""
        updated = Notification.objects.filter(id=notification_id, recipient=user).update(
            is_read=True,
            read_at=timezone.now()
        )
        return updated > 0

    @classmethod
    def mark_all_as_read(cls, user) -> int:
        """Marks all pending notifications as read for a given user."""
        return Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
