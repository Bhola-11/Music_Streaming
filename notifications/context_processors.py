"""
Context processor to expose unread notifications count.
"""
from .models import Notification


def unread_notifications(request):
    if request.user.is_authenticated:
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {'UNREAD_NOTIFICATIONS_COUNT': count}
    return {'UNREAD_NOTIFICATIONS_COUNT': 0}
