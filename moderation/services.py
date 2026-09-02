"""
Moderation Service: Takedown Automation, Quarantine Workflows & Audit Logging.
"""
from django.utils import timezone
from .models import ModerationReport, TakedownRequest, ModerationStatus
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity
from notifications.services import NotificationService
from notifications.models import NotificationType


class ModerationService:
    """
    Workflows for content quarantine, takedown approval, and DMCA execution.
    """

    @classmethod
    def execute_takedown(cls, report: ModerationReport, moderator_user, reason_notes: str) -> bool:
        """
        Quarantines/unpublishes infringing media and notifies the uploader.
        """
        report.status = ModerationStatus.RESOLVED_REMOVED
        report.reviewed_by = moderator_user
        report.resolution_notes = reason_notes
        report.resolved_at = timezone.now()
        report.save()

        # Unpublish song
        if report.song:
            song = report.song
            song.is_published = False
            song.save(update_fields=['is_published'])

            # Notify the artist owner
            if hasattr(song.artist, 'user') and song.artist.user:
                NotificationService.send_notification(
                    recipient=song.artist.user,
                    notification_type=NotificationType.SECURITY_ALERT,
                    title="Track Quarantined / Takedown Notice",
                    message=f"Your track '{song.title}' was taken down due to: {reason_notes}"
                )

        # Audit log privileged admin action
        AuditService.log_admin_action(
            admin_user=moderator_user,
            action='moderation.takedown_executed',
            target_entity=f"Report:{report.id}",
            justification_reason=reason_notes
        )
        return True

    @classmethod
    def dismiss_report(cls, report: ModerationReport, moderator_user, reason_notes: str) -> bool:
        report.status = ModerationStatus.RESOLVED_DISMISSED
        report.reviewed_by = moderator_user
        report.resolution_notes = reason_notes
        report.resolved_at = timezone.now()
        report.save()

        AuditService.log_admin_action(
            admin_user=moderator_user,
            action='moderation.report_dismissed',
            target_entity=f"Report:{report.id}",
            justification_reason=reason_notes
        )
        return True
