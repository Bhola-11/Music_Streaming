"""
Algorithmic Recommendations Models: User Taste Profiles, Track Vector Similarities,
Personalized Daily Mixes, and Recommendation History.
"""
import uuid
from django.db import models
from django.conf import settings


class UserTasteProfile(models.Model):
    """
    Synthesized machine learning taste vector based on user listening habits.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='taste_profile')
    top_genres = models.JSONField(default=list, blank=True, help_text='Array of top genre slugs with affinity scores')
    top_artists = models.JSONField(default=list, blank=True)
    preferred_min_bpm = models.PositiveSmallIntegerField(default=80)
    preferred_max_bpm = models.PositiveSmallIntegerField(default=160)
    diversity_score = models.FloatField(default=0.5, help_text='Tendency to explore new versus familiar tracks (0.0 to 1.0)')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Taste Profile for {self.user.username}"


class TrackSimilarity(models.Model):
    """
    Precomputed pairwise cosine similarity between songs based on audio features.
    """
    source_song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='similarities_from')
    target_song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='similarities_to')
    similarity_score = models.FloatField(default=0.0, db_index=True)

    class Meta:
        unique_together = ('source_song', 'target_song')
        indexes = [
            models.Index(fields=['source_song', '-similarity_score']),
        ]

    def __str__(self):
        return f"{self.source_song.title} <-> {self.target_song.title} ({self.similarity_score:.2f})"


class DailyMix(models.Model):
    """
    Algorithmically generated personal mixtape updated daily/weekly for each user.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_mixes')
    mix_number = models.PositiveSmallIntegerField(default=1)  # Daily Mix 1, Daily Mix 2, Discover Weekly
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=250, blank=True)
    cover_image_url = models.URLField(blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'mix_number')
        ordering = ['mix_number']

    def __str__(self):
        return f"{self.title} for {self.user.username}"


class DailyMixTrack(models.Model):
    """
    Tracks within a personalized Daily Mix.
    """
    mix = models.ForeignKey(DailyMix, on_delete=models.CASCADE, related_name='tracks')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['position']
        unique_together = ('mix', 'song')

    def __str__(self):
        return f"#{self.position} - {self.song.title} in {self.mix.title}"


class RecommendationHistory(models.Model):
    """
    Telemetry on recommendation impressions, clicks, and stream completions.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE)
    algorithm_source = models.CharField(max_length=50, default='collaborative_filter')
    was_clicked = models.BooleanField(default=False)
    was_completed = models.BooleanField(default=False)
    recommended_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recommended_at']
