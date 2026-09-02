"""
Discovery & Search Engine Models: Trending Metrics, FeaturedBanners,
Music Charts, Chart Entries, and Search Query Analytics.
"""
import uuid
from django.db import models
from django.conf import settings


class ChartType(models.TextChoices):
    TOP_50_GLOBAL = 'top_50_global', 'Global Top 50'
    VIRAL_TRENDING = 'viral_trending', 'Viral Trending 50'
    GENRE_SPOTLIGHT = 'genre_spotlight', 'Genre Spotlight'
    NEW_DISCOVERY = 'new_discovery', 'Fresh Discoveries'


class FeaturedBanner(models.Model):
    """
    Hero banner highlights displayed on the Discovery Hub and Homepage.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    subtitle = models.CharField(max_length=250, blank=True)
    badge_text = models.CharField(max_length=50, default='FEATURED RELEASE')
    banner_image = models.ImageField(upload_to='banners/%Y/%m/', blank=True, null=True)
    action_url = models.CharField(max_length=255)
    action_button_text = models.CharField(max_length=50, default='Listen Now')
    is_active = models.BooleanField(default=True, db_index=True)
    display_order = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', '-created_at']

    def __str__(self):
        return f"Banner: {self.title}"

    @property
    def banner_image_url(self):
        if self.banner_image and hasattr(self.banner_image, 'url'):
            return self.banner_image.url
        return 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=1200&auto=format&fit=crop&q=80'


class MusicChart(models.Model):
    """
    Curated and algorithmically generated streaming charts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=150, unique=True)
    chart_type = models.CharField(max_length=30, choices=ChartType.choices, default=ChartType.TOP_50_GLOBAL)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='charts/%Y/%m/', blank=True, null=True)
    is_published = models.BooleanField(default=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def cover_art_url(self):
        if self.cover_image and hasattr(self.cover_image, 'url'):
            return self.cover_image.url
        return 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&auto=format&fit=crop&q=80'


class ChartEntry(models.Model):
    """
    An entry in a music chart with rank, previous rank, and peak rank metrics.
    """
    chart = models.ForeignKey(MusicChart, on_delete=models.CASCADE, related_name='entries')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField(db_index=True)
    previous_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    peak_rank = models.PositiveSmallIntegerField(default=1)
    weeks_on_chart = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['rank']
        unique_together = ('chart', 'song')

    def __str__(self):
        return f"#{self.rank} - {self.song.title} in {self.chart.title}"

    @property
    def rank_change(self):
        if not self.previous_rank:
            return 'NEW'
        if self.rank < self.previous_rank:
            return f"+{self.previous_rank - self.rank}"
        if self.rank > self.previous_rank:
            return f"-{self.rank - self.previous_rank}"
        return '='


class TrendingMetric(models.Model):
    """
    Rolling audio stream velocity metrics to compute viral acceleration.
    """
    song = models.OneToOneField('music.Song', on_delete=models.CASCADE, related_name='trending_metric')
    velocity_score = models.FloatField(default=0.0, db_index=True)
    streams_last_24h = models.PositiveIntegerField(default=0)
    streams_last_7d = models.PositiveIntegerField(default=0)
    calculated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.song.title} (Velocity: {self.velocity_score:.2f})"


class SearchQueryLog(models.Model):
    """
    Search telemetry log for analyzing search trends, autocomplete, and typos.
    """
    query_text = models.CharField(max_length=200, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    results_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Query '{self.query_text}' ({self.results_count} hits)"
