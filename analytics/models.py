from django.apps import AppConfig
from django.db import models
import uuid


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'
    verbose_name = 'Analytics & Insights'


class DailyPlayCount(models.Model):
    date = models.DateField(db_index=True)
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='daily_stats')
    total_plays = models.PositiveIntegerField(default=0)
    unique_listeners = models.PositiveIntegerField(default=0)
    complete_plays = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('date', 'song')
        ordering = ['-date']


class ArtistEarningsDaily(models.Model):
    date = models.DateField(db_index=True)
    artist = models.ForeignKey('artists.Artist', on_delete=models.CASCADE, related_name='daily_earnings')
    stream_count = models.PositiveIntegerField(default=0)
    estimated_revenue_usd = models.DecimalField(max_digits=10, decimal_places=4, default=0.0)

    class Meta:
        unique_together = ('date', 'artist')
        ordering = ['-date']
