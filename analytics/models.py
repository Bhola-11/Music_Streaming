"""
Platform Analytics Models: Daily Metrics, Stream Farm Anomalies,
Genre Distributions & Geographic Heatmaps.
"""
import uuid
from django.db import models


class DailyPlatformMetric(models.Model):
    """
    Daily aggregated stream counts, active users, storage usage, and bandwidth metrics.
    """
    date = models.DateField(unique=True, db_index=True)
    total_streams = models.PositiveBigIntegerField(default=0)
    unique_listeners = models.PositiveIntegerField(default=0)
    new_users_registered = models.PositiveIntegerField(default=0)
    new_tracks_uploaded = models.PositiveIntegerField(default=0)
    bandwidth_served_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    royalty_accrued_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Metrics for {self.date}: {self.total_streams} streams, {self.unique_listeners} listeners"


class StreamGeoHeatmap(models.Model):
    """
    Geographic distribution of streams by country.
    """
    country_code = models.CharField(max_length=5, db_index=True)
    country_name = models.CharField(max_length=100)
    stream_count = models.PositiveBigIntegerField(default=0)
    listener_count = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-stream_count']

    def __str__(self):
        return f"{self.country_name} ({self.country_code}): {self.stream_count} streams"


class SuspiciousActivityFlag(models.Model):
    """
    Automated stream farm and bot inflation detection logs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    target_song = models.ForeignKey('music.Song', on_delete=models.CASCADE, null=True, blank=True)
    target_artist = models.ForeignKey('artists.Artist', on_delete=models.CASCADE, null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    flag_reason = models.CharField(max_length=200)
    stream_burst_count = models.PositiveIntegerField(default=0)
    is_blocked = models.BooleanField(default=True)
    flagged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-flagged_at']

    def __str__(self):
        return f"Flag: {self.flag_reason} on {self.ip_address} ({self.stream_burst_count} plays)"
