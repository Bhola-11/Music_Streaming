"""
Context Processor for exposing Unread Notification Count to all templates.
"""
from .models import Notification


def notification_context(request):
    """
    Injects unread_notifications_count and top recent unread notifications into every template context.
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        recent_notifications = Notification.objects.filter(recipient=request.user)[:5]
        return {
            'unread_notifications_count': unread_count,
            'UNREAD_NOTIFICATIONS_COUNT': unread_count,
            'recent_notifications': recent_notifications,
        }
    return {
        'unread_notifications_count': 0,
        'UNREAD_NOTIFICATIONS_COUNT': 0,
        'recent_notifications': [],
    }


unread_notifications = notification_context

