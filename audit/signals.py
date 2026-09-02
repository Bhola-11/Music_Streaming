"""
Audit Signals to intercept Django core auth events and log them securely.
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from .services import AuditService
from .models import ActionCategory, ActionSeverity


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = request.META.get('REMOTE_ADDR', '127.0.0.1') if request else '127.0.0.1'
    ua = request.META.get('HTTP_USER_AGENT', '') if request else ''
    AuditService.log_action(
        action_type='user.login.success',
        category=ActionCategory.AUTHENTICATION,
        severity=ActionSeverity.INFO,
        description=f"User {user.email} successfully logged in",
        user=user,
        ip_address=ip,
        user_agent=ua,
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1') if request else '127.0.0.1'
        ua = request.META.get('HTTP_USER_AGENT', '') if request else ''
        AuditService.log_action(
            action_type='user.logout',
            category=ActionCategory.AUTHENTICATION,
            severity=ActionSeverity.INFO,
            description=f"User {user.email} logged out",
            user=user,
            ip_address=ip,
            user_agent=ua,
        )


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    ip = request.META.get('REMOTE_ADDR', '127.0.0.1') if request else '127.0.0.1'
    ua = request.META.get('HTTP_USER_AGENT', '') if request else ''
    attempted_identity = credentials.get('email') or credentials.get('username') or 'unknown'
    
    AuditService.log_security_event(
        event_type='user.login.failed',
        severity=ActionSeverity.MEDIUM,
        source_ip=ip,
        user_agent=ua,
        details={'attempted_identity': attempted_identity}
    )
