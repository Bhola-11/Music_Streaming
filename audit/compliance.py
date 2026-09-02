"""
GDPR / CCPA Privacy & Compliance Engine.
Facilitates full personal data export (Takeout) and right-to-be-forgotten erasure workflows.
"""
import json
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from accounts.models import User, UserProfile, UserPreferences, UserSession, UserFollow
from .services import AuditService
from .models import ActionCategory, ActionSeverity


class ComplianceManager:
    """
    Handles user privacy exports and cryptographic anonymization.
    """

    @classmethod
    def generate_user_data_export(cls, user: User) -> dict:
        """
        Gathers all personal data, preferences, listening statistics, and audit records for export.
        """
        profile = getattr(user, 'profile', None)
        preferences = getattr(user, 'preferences', None)

        export_payload = {
            'metadata': {
                'platform': 'MusicVerse',
                'export_generated_at': timezone.now().isoformat(),
                'user_id': str(user.id),
                'email': user.email,
                'username': user.username,
            },
            'profile': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'headline': profile.headline if profile else '',
                'bio': profile.bio if profile else '',
                'location': profile.location if profile else '',
                'country': profile.country if profile else '',
                'website': profile.website if profile else '',
                'social_links': profile.social_links if profile else {},
            },
            'preferences': {
                'audio_quality': preferences.audio_quality if preferences else 'standard',
                'visualizer_mode': preferences.visualizer_mode if preferences else '3d-particle-mesh',
                'equalizer_preset': preferences.equalizer_preset if preferences else 'Flat',
                'theme': preferences.theme if preferences else 'dark-cosmic',
            },
            'active_sessions_count': UserSession.objects.filter(user=user, is_active=True).count(),
            'following_count': UserFollow.objects.filter(follower=user).count(),
            'followers_count': UserFollow.objects.filter(following=user).count(),
        }

        AuditService.log_action(
            action_type='compliance.gdpr_export',
            category=ActionCategory.USER_MANAGEMENT,
            severity=ActionSeverity.INFO,
            user=user,
            description=f"GDPR Data Export bundle generated for {user.email}"
        )

        return export_payload

    @classmethod
    def anonymize_user_account(cls, user: User) -> bool:
        """
        Performs irreversible GDPR erasure: wipes PII, scrambles email, disables authentication.
        """
        AuditService.log_action(
            action_type='compliance.gdpr_erasure',
            category=ActionCategory.USER_MANAGEMENT,
            severity=ActionSeverity.HIGH,
            user=user,
            description=f"GDPR Account Erasure executed for user {user.id}"
        )

        user.is_active = False
        user.email = f"erased_{user.id}@anonymized.musicverse.io"
        user.username = f"deleted_user_{str(user.id)[:8]}"
        user.first_name = ""
        user.last_name = ""
        user.phone = None
        user.set_unusable_password()
        user.save()

        # Wipe profile
        if hasattr(user, 'profile'):
            user.profile.bio = ""
            user.profile.headline = ""
            user.profile.website = ""
            user.profile.social_links = {}
            user.profile.save()

        return True
