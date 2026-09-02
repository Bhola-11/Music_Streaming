"""
User Activity & Session Tracking Middleware.
Tracks active user devices and records last activity timestamp.
"""
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from .models import UserSession


class UserActivityMiddleware(MiddlewareMixin):
    """
    Updates the last_activity timestamp on active user sessions.
    """

    def process_request(self, request):
        if request.user.is_authenticated and request.session.session_key:
            session_key = request.session.session_key
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            ua = request.META.get('HTTP_USER_AGENT', '')

            device_type = 'Desktop Browser'
            if 'Mobile' in ua or 'Android' in ua or 'iPhone' in ua:
                device_type = 'Mobile Device'
            elif 'iPad' in ua or 'Tablet' in ua:
                device_type = 'Tablet'

            session_obj, created = UserSession.objects.get_or_create(
                session_key=session_key,
                defaults={
                    'user': request.user,
                    'ip_address': ip,
                    'user_agent': ua,
                    'device_type': device_type,
                    'is_active': True,
                    'last_activity': timezone.now()
                }
            )
            if not created:
                # Update timestamp if more than 5 minutes elapsed
                if (timezone.now() - session_obj.last_activity).total_seconds() > 300:
                    session_obj.last_activity = timezone.now()
                    session_obj.save(update_fields=['last_activity'])
