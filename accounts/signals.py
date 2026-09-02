"""
Account Signals for automatic profile instantiation, preferences initialization,
and audit record triggers.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserProfile, UserPreferences
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


@receiver(post_save, sender=User)
def create_or_save_user_related_models(sender, instance, created, **kwargs):
    """
    Ensures every newly registered user automatically gets an attached
    UserProfile and UserPreferences instance.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
        UserPreferences.objects.get_or_create(user=instance)
        
        # Log audit action
        AuditService.log_action(
            action_type='user.registered',
            category=ActionCategory.USER_MANAGEMENT,
            severity=ActionSeverity.INFO,
            description=f"New user account created: {instance.username} ({instance.email})",
            user=instance,
            target_model='User',
            target_object_id=str(instance.id),
            target_repr=instance.username
        )
    else:
        # If user is modified
        if hasattr(instance, 'profile'):
            instance.profile.save()
        if hasattr(instance, 'preferences'):
            instance.preferences.save()
