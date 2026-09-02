"""
Audit Decorators for view protection and targeted action tracking.
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .services import AuditService
from .models import ActionCategory, ActionSeverity


def audit_action(action_type: str, category: str = ActionCategory.USER_MANAGEMENT, severity: str = ActionSeverity.INFO):
    """
    Decorator for Django view functions to automatically log action execution.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            
            ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
            if ',' in ip:
                ip = ip.split(',')[0].strip()

            AuditService.log_action(
                action_type=action_type,
                category=category,
                severity=severity,
                description=f"Action '{action_type}' triggered via {view_func.__name__}",
                user=request.user if request.user.is_authenticated else None,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_method=request.method,
                request_path=request.path,
                status_code=getattr(response, 'status_code', 200),
            )
            return response
        return _wrapped_view
    return decorator


def require_audit_reason(view_func):
    """
    Ensures POST requests to sensitive endpoints contain a non-empty 'audit_reason' field.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method == 'POST' and not request.POST.get('audit_reason', '').strip():
            messages.error(request, "A valid justification reason is required for this action.")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        return view_func(request, *args, **kwargs)
    return _wrapped_view
