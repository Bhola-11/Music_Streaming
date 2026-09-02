"""
Security Anomaly & Threat Detection Engine.
Applies heuristic pattern matching and anomaly rules to identify compromised accounts,
credential stuffing attacks, and fraudulent streaming farms.
"""
from django.utils import timezone
from django.db.models import Count
from .models import AuditLog, SecurityEvent, ActionSeverity
from .services import AuditService


class SecurityAnomalyDetector:
    """
    Automated anomaly scanner executed periodically or synchronously on suspicious triggers.
    """

    @classmethod
    def scan_ip_reputation(cls, ip_address: str, threshold_fails: int = 10) -> bool:
        """
        Detects if an IP address has triggered excessive failed authentication attempts in 1 hour.
        """
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        failure_count = SecurityEvent.objects.filter(
            source_ip=ip_address,
            event_type__icontains='failed',
            created_at__gte=one_hour_ago
        ).count()

        if failure_count >= threshold_fails:
            AuditService.log_security_event(
                event_type='ip_brute_force_block',
                severity=ActionSeverity.CRITICAL,
                source_ip=ip_address,
                details={'recent_failures_1h': failure_count}
            )
            return True
        return False

    @classmethod
    def detect_impossible_travel(cls, user, new_ip: str, new_country: str) -> bool:
        """
        Detects if a user logs in from two distant geographic locations within an impossible timeframe.
        """
        last_event = SecurityEvent.objects.filter(user=user).order_by('-created_at').first()
        if not last_event:
            return False

        time_delta = (timezone.now() - last_event.created_at).total_seconds()
        
        # If country changed in less than 30 minutes
        if last_event.country_code != 'XX' and new_country != 'XX':
            if last_event.country_code != new_country and time_delta < 1800:
                AuditService.log_security_event(
                    event_type='impossible_travel_detected',
                    severity=ActionSeverity.CRITICAL,
                    user=user,
                    source_ip=new_ip,
                    country_code=new_country,
                    details={
                        'previous_country': last_event.country_code,
                        'previous_ip': last_event.source_ip,
                        'elapsed_seconds': time_delta
                    }
                )
                return True
        return False

    @classmethod
    def detect_streaming_farm_anomaly(cls, user, streams_in_10min: int = 150) -> bool:
        """
        Identifies artificial stream inflation / bot activity on artist accounts.
        """
        if streams_in_10min > 120:
            AuditService.log_security_event(
                event_type='stream_inflation_bot_detected',
                severity=ActionSeverity.HIGH,
                user=user,
                details={'burst_stream_count': streams_in_10min}
            )
            return True
        return False
