"""
Audit Trail Middleware.
Automatically captures state changes, critical endpoint accesses, and user network telemetry.
"""
from django.utils.deprecation import MiddlewareMixin
from .services import AuditService
from .models import ActionCategory, ActionSeverity


class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Monitors incoming HTTP requests and generates structured audit logs
    for state-changing methods (POST, PUT, PATCH, DELETE) and administrative views.
    """

    EXCLUDED_PREFIXES = (
        '/static/',
        '/media/',
        '/favicon.ico',
        '/health/',
    )

    CRITICAL_ROUTES = {
        '/accounts/login/': ('auth.login_attempt', ActionCategory.AUTHENTICATION, ActionSeverity.INFO),
        '/accounts/logout/': ('auth.logout', ActionCategory.AUTHENTICATION, ActionSeverity.INFO),
        '/accounts/register/': ('auth.register_attempt', ActionCategory.AUTHENTICATION, ActionSeverity.INFO),
        '/accounts/password-reset/': ('auth.password_reset_request', ActionCategory.AUTHENTICATION, ActionSeverity.LOW),
        '/payments/checkout/': ('payment.checkout_initiated', ActionCategory.FINANCIAL, ActionSeverity.MEDIUM),
        '/moderation/takedown/': ('moderation.takedown_filed', ActionCategory.MODERATION, ActionSeverity.HIGH),
    }

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip

    def process_response(self, request, response):
        path = request.path

        # Ignore static and health routes
        if any(path.startswith(prefix) for prefix in self.EXCLUDED_PREFIXES):
            return response

        # Audit critical auth or financial paths
        if path in self.CRITICAL_ROUTES and request.method == 'POST':
            action_type, category, severity = self.CRITICAL_ROUTES[path]
            user = request.user if request.user.is_authenticated else None
            ip = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            AuditService.log_action(
                action_type=action_type,
                category=category,
                severity=severity,
                description=f"Path {path} accessed with status {response.status_code}",
                user=user,
                ip_address=ip,
                user_agent=user_agent,
                request_method=request.method,
                request_path=path,
                status_code=response.status_code,
            )

        # Audit admin panel mutations
        elif path.startswith('/admin/') and request.method in ('POST', 'PUT', 'DELETE'):
            user = request.user if request.user.is_authenticated else None
            ip = self._get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

            AuditService.log_action(
                action_type='admin.mutation',
                category=ActionCategory.SYSTEM_CONFIG,
                severity=ActionSeverity.MEDIUM,
                description=f"Admin modification at {path}",
                user=user,
                ip_address=ip,
                user_agent=user_agent,
                request_method=request.method,
                request_path=path,
                status_code=response.status_code,
            )

        return response
