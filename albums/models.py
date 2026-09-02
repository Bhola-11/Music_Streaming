"""
Albums, Discography, Editions, Track Listings & Review Models.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class RecordLabel(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=170, unique=True)
    country = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='labels/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AlbumType(models.TextChoices):
    LP = 'lp', 'Full Studio Album (LP)'
    EP = 'ep', 'Extended Play (EP)'
    SINGLE = 'single', 'Single Track Release'
    COMPILATION = 'compilation', 'Compilation / Anthology'
    LIVE = 'live', 'Live Concert Recording'
    REMIX = 'remix', 'Remix Collection'


class Album(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=240, db_index=True)
    artist = models.ForeignKey('artists.Artist', on_delete=models.CASCADE, related_name='albums')
    album_type = models.CharField(max_length=20, choices=AlbumType.choices, default=AlbumType.LP)
    record_label = models.ForeignKey(RecordLabel, on_delete=models.SET_NULL, null=True, blank=True, related_name='releases')
    
    cover_art = models.ImageField(upload_to='covers/albums/%Y/%m/', blank=True, null=True)
    release_date = models.DateField(null=True, blank=True, db_index=True)
    upc_code = models.CharField(max_length=30, blank=True, help_text='Universal Product Code')
    description = models.TextField(blank=True)
    copyright_line = models.CharField(max_length=255, blank=True)
    
    total_discs = models.PositiveSmallIntegerField(default=1)
    is_published = models.BooleanField(default=True, db_index=True)
    is_explicit = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.artist.name}-{self.title}")
            self.slug = f"{base_slug}-{str(self.id)[:6]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} — {self.artist.name} ({self.get_album_type_display()})"

    @property
    def cover_art_url(self):
        if self.cover_art and hasattr(self.cover_art, 'url'):
            return self.cover_art.url
        return 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400&auto=format&fit=crop&q=80'

    @property
    def total_duration_seconds(self):
        return sum(item.song.duration_seconds for item in self.album_tracks.select_related('song') if item.song)

    @property
    def formatted_total_duration(self):
        total = self.total_duration_seconds
        mins = total // 60
        secs = total % 60
        return f"{mins} min {secs} sec"


class AlbumTrack(models.Model):
    """
    Junction between Album and Song to support track numbering, disc assignments, and sequencing.
    """
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='album_tracks')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='album_associations')
    disc_number = models.PositiveSmallIntegerField(default=1)
    track_number = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['disc_number', 'track_number']
        unique_together = ('album', 'disc_number', 'track_number')

    def __str__(self):
        return f"Disc {self.disc_number} Track {self.track_number}: {self.song.title}"


class DiscEdition(models.Model):
    """
    Special editions of an album (e.g. Deluxe Edition with bonus stems, 24-bit Vinyl Remaster).
    """
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='editions')
    edition_name = models.CharField(max_length=100)  # e.g., Deluxe Remaster, Spatial Audio Mix
    bonus_features = models.TextField(blank=True)
    is_hi_res_exclusive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.album.title} [{self.edition_name}]"


class AlbumReview(models.Model):
    """
    Community reviews and critique ratings for albums.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='album_reviews')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    title = models.CharField(max_length=150)
    body = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('album', 'user')

    def __str__(self):
        return f"Review on {self.album.title} by {self.user.username} ({self.rating}/10)"
