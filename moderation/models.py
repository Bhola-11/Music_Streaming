"""
Content Moderation & DMCA Takedown Models: Reports, Copyright Claims,
Content Filter Rules & Moderator Audit Logs.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


class ReportReason(models.TextChoices):
    COPYRIGHT_DMCA = 'copyright_dmca', 'Copyright Infringement (DMCA)'
    EXPLICIT_UNMARKED = 'explicit_unmarked', 'Unmarked Explicit / Mature Content'
    HATE_SPEECH = 'hate_speech', 'Hate Speech / Harassment'
    AUDIO_LEAK = 'audio_leak', 'Unreleased / Leaked Audio'
    SPAM_OR_SCAM = 'spam', 'Spam / Fake Content'
    OTHER = 'other', 'Other Violation'


class ModerationStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Review'
    INVESTIGATING = 'investigating', 'Under Investigation'
    RESOLVED_REMOVED = 'removed', 'Content Taken Down'
    RESOLVED_DISMISSED = 'dismissed', 'Report Dismissed (No Violation)'


class ModerationReport(models.Model):
    """
    User-submitted report flagging a track, artist, album, or comment.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='filed_reports')
    reason = models.CharField(max_length=30, choices=ReportReason.choices, default=ReportReason.COPYRIGHT_DMCA, db_index=True)
    status = models.CharField(max_length=20, choices=ModerationStatus.choices, default=ModerationStatus.PENDING, db_index=True)
    
    # Target entities
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, null=True, blank=True, related_name='moderation_reports')
    artist = models.ForeignKey('artists.Artist', on_delete=models.CASCADE, null=True, blank=True, related_name='moderation_reports')
    album = models.ForeignKey('albums.Album', on_delete=models.CASCADE, null=True, blank=True, related_name='moderation_reports')
    comment = models.ForeignKey('music.TrackComment', on_delete=models.CASCADE, null=True, blank=True, related_name='moderation_reports')
    
    description = models.TextField(max_length=1500)
    evidence_url = models.URLField(blank=True)
    
    # Review details
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_moderation_reports')
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report #{str(self.id)[:8]} ({self.get_reason_display()}) - {self.get_status_display()}"


class TakedownRequest(models.Model):
    """
    Formal DMCA Copyright Claim submitted by copyright holders or record labels.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claimant_name = models.CharField(max_length=150)
    claimant_email = models.EmailField()
    copyright_owner = models.CharField(max_length=150)
    infringing_song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='dmca_requests')
    work_title = models.CharField(max_length=200, help_text='Original copyrighted work title')
    statement_of_authority = models.BooleanField(default=True, help_text='Statement made under penalty of perjury')
    
    status = models.CharField(max_length=20, choices=ModerationStatus.choices, default=ModerationStatus.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    actioned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"DMCA Claim for {self.infringing_song.title} by {self.claimant_name}"


class ContentFilterRule(models.Model):
    """
    Automated keyword and acoustic pattern filter for hate speech and spam detection.
    """
    keyword_pattern = models.CharField(max_length=100, unique=True)
    is_regex = models.BooleanField(default=False)
    severity_level = models.CharField(max_length=20, default='HIGH')
    auto_quarantine = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Filter Rule: {self.keyword_pattern}"
