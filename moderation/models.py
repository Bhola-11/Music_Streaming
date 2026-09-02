from django.apps import AppConfig
from django.db import models
from django.conf import settings
import uuid


class ModerationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'moderation'
    verbose_name = 'Content Moderation & DMCA'


class ContentReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='filed_reports')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    reason = models.CharField(max_length=100)
    details = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
