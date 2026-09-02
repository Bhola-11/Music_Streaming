"""
Service Layer for Audit Trail, Telemetry and Security Event Logging.
"""
import hashlib
import json
import logging
from django.utils import timezone
from django.db.models import Count, Q
from django.core.serializers.json import DjangoJSONEncoder
from .models import AuditLog, SecurityEvent, APIRequestLog, AdminActionLog, ActionCategory, ActionSeverity

logger = logging.getLogger('musicverse.audit')


class AuditService:
    """
    Central orchestrator for recording structured, tamper-evident audit logs.
    """

    @staticmethod
    def calculate_signature(payload: dict) -> str:
        """Computes a SHA-256 integrity hash for an audit record."""
        serialized = json.dumps(payload, sort_keys=True, cls=DjangoJSONEncoder)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    @classmethod
    def log_action(
        cls,
        action_type: str,
        category: str = ActionCategory.AUTHENTICATION,
        severity: str = ActionSeverity.INFO,
        description: str = '',
        user=None,
        target_model: str = None,
        target_object_id: str = None,
        target_repr: str = None,
        ip_address: str = None,
        user_agent: str = None,
        request_method: str = 'GET',
        request_path: str = '',
        status_code: int = None,
        pre_change_state: dict = None,
        post_change_state: dict = None,
        metadata: dict = None,
    ) -> AuditLog:
        """
        Creates and persists an immutable audit log record.
        """
        actor_email = user.email if (user and hasattr(user, 'email') and user.is_authenticated) else None
        actor_role = getattr(user, 'role', 'anonymous') if (user and user.is_authenticated) else 'anonymous'

        metadata_payload = metadata or {}

        payload_for_signature = {
            'action_type': action_type,
            'category': category,
            'actor_email': actor_email,
            'target_model': target_model,
            'target_object_id': str(target_object_id) if target_object_id else None,
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat(),
        }
        signature = cls.calculate_signature(payload_for_signature)

        audit_entry = AuditLog.objects.create(
            user=user if (user and user.is_authenticated) else None,
            actor_email=actor_email,
            actor_role=actor_role,
            category=category,
            severity=severity,
            action_type=action_type,
            description=description or f"Action {action_type} executed by {actor_email or 'system'}",
            target_model=target_model,
            target_object_id=str(target_object_id) if target_object_id else None,
            target_repr=target_repr[:255] if target_repr else None,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else '',
            request_method=request_method,
            request_path=request_path[:500],
            status_code=status_code,
            pre_change_state=pre_change_state,
            post_change_state=post_change_state,
            metadata=metadata_payload,
            signature=signature,
        )
        return audit_entry

    @classmethod
    def log_security_event(
        cls,
        event_type: str,
        severity: str = ActionSeverity.HIGH,
        user=None,
        source_ip: str = '127.0.0.1',
        user_agent: str = '',
        details: dict = None,
        country_code: str = 'XX',
        city: str = 'Unknown'
    ) -> SecurityEvent:
        """
        Records high-priority threat intelligence and security incident anomalies.
        """
        sec_event = SecurityEvent.objects.create(
            user=user if (user and user.is_authenticated) else None,
            event_type=event_type,
            severity=severity,
            source_ip=source_ip or '127.0.0.1',
            user_agent=user_agent or '',
            country_code=country_code,
            city=city,
            details=details or {},
        )
        logger.warning(f"[SECURITY_ALERT] Type: {event_type} from {source_ip} | Severity: {severity}")
        return sec_event

    @classmethod
    def log_admin_action(
        cls,
        admin_user,
        action: str,
        target_entity: str,
        justification_reason: str,
        changes_applied: dict = None
    ) -> AdminActionLog:
        """
        Mandatory logging for privileged staff operations.
        """
        return AdminActionLog.objects.create(
            admin_user=admin_user,
            action=action,
            target_entity=target_entity,
            justification_reason=justification_reason,
            changes_applied=changes_applied or {}
        )

    @staticmethod
    def get_security_summary():
        """
        Aggregates security metrics for administrator dashboards.
        """
        total_logs = AuditLog.objects.count()
        unresolved_security_events = SecurityEvent.objects.filter(is_resolved=False).count()
        critical_events = SecurityEvent.objects.filter(severity=ActionSeverity.CRITICAL).count()
        recent_failures = SecurityEvent.objects.filter(
            event_type__icontains='failed_login',
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()

        category_distribution = list(
            AuditLog.objects.values('category').annotate(count=Count('id')).order_by('-count')
        )

        return {
            'total_logs': total_logs,
            'unresolved_security_events': unresolved_security_events,
            'critical_events': critical_events,
            'recent_failures': recent_failures,
            'category_distribution': category_distribution,
        }
