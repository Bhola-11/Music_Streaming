"""
Music Catalog & Audio Asset Models.
Implements Song, Multi-Format Audio Files, Waveform Peaks, Synced LRC Lyrics,
Song Contributors, Track Ratings, and Comments.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class Genre(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=60, unique=True, db_index=True)
    slug = models.SlugField(max_length=80, unique=True, db_index=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='genres/', blank=True, null=True)
    color_hex = models.CharField(max_length=7, default='#00F5D4')
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Mood(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    icon = models.CharField(max_length=10, default='✨')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.icon} {self.name}"


class AudioFormatType(models.TextChoices):
    MP3_STANDARD = 'mp3_320', 'MP3 (320 kbps High Quality)'
    FLAC_LOSSLESS = 'flac_1411', 'FLAC (1411 kbps Studio Master Lossless)'
    AAC_SAVER = 'aac_96', 'AAC (96 kbps Data Saver)'
    WAV_STEM = 'wav_raw', 'WAV Master Stem'


class Song(models.Model):
    """
    Primary musical entity containing technical specs, metadata, and audio files.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=240, db_index=True)
    artist = models.ForeignKey('artists.Artist', on_delete=models.CASCADE, related_name='songs')
    album = models.ForeignKey('albums.Album', on_delete=models.SET_NULL, null=True, blank=True, related_name='tracks')
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, related_name='songs')
    moods = models.ManyToManyField(Mood, blank=True, related_name='songs')
    
    # Audio master file
    audio_file = models.FileField(upload_to='audio/masters/%Y/%m/', blank=True)
    cover_art = models.ImageField(upload_to='covers/songs/%Y/%m/', blank=True, null=True)
    
    # Technical audio properties
    duration_seconds = models.PositiveIntegerField(default=0, help_text='Duration in seconds')
    bitrate_kbps = models.PositiveIntegerField(default=320)
    sample_rate_hz = models.PositiveIntegerField(default=44100)
    channels = models.PositiveSmallIntegerField(default=2)
    bpm = models.PositiveSmallIntegerField(null=True, blank=True, help_text='Beats per minute (tempo)')
    musical_key = models.CharField(max_length=10, blank=True, help_text='e.g., C Major, F# Minor')
    
    # Content flags
    is_explicit = models.BooleanField(default=False)
    is_premium_only = models.BooleanField(default=False, db_index=True)
    is_published = models.BooleanField(default=True, db_index=True)
    is_original_master = models.BooleanField(default=True)
    release_date = models.DateField(null=True, blank=True)
    
    # Statistics & Engagement
    play_count = models.PositiveBigIntegerField(default=0, db_index=True)
    like_count = models.PositiveIntegerField(default=0, db_index=True)
    waveform_data = models.JSONField(default=list, blank=True, help_text='Array of normalized float amplitude peaks')
    
    # Licensing / Copyright
    isrc_code = models.CharField(max_length=20, blank=True, help_text='International Standard Recording Code')
    copyright_line = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['artist', 'is_published']),
            models.Index(fields=['genre', 'play_count']),
            models.Index(fields=['is_premium_only', 'is_published']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.artist.name}-{self.title}")
            self.slug = f"{base_slug}-{str(self.id)[:6]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} — {self.artist.name}"

    @property
    def formatted_duration(self):
        mins = self.duration_seconds // 60
        secs = self.duration_seconds % 60
        return f"{mins}:{secs:02d}"

    @property
    def cover_art_url(self):
        if self.cover_art and hasattr(self.cover_art, 'url'):
            return self.cover_art.url
        if self.album and self.album.cover_art and hasattr(self.album.cover_art, 'url'):
            return self.album.cover_art.url
        return 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300&auto=format&fit=crop&q=80'


class SongFile(models.Model):
    """
    Different encoded quality formats for a single song (Lossless FLAC, Standard MP3, Data Saver AAC).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='encoded_files')
    format_type = models.CharField(max_length=20, choices=AudioFormatType.choices, default=AudioFormatType.MP3_STANDARD)
    file = models.FileField(upload_to='audio/encoded/%Y/%m/')
    bitrate_kbps = models.PositiveIntegerField(default=320)
    file_size_bytes = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('song', 'format_type')

    def __str__(self):
        return f"{self.song.title} ({self.get_format_type_display()})"


class Lyrics(models.Model):
    """
    Stores plain text and timestamped LRC synchronized lyrics for interactive sing-along.
    """
    song = models.OneToOneField(Song, on_delete=models.CASCADE, related_name='lyrics')
    plain_lyrics = models.TextField(help_text='Unsynchronized full song lyrics')
    is_synced = models.BooleanField(default=False)
    synced_lyrics_json = models.JSONField(
        default=list,
        blank=True,
        help_text='Array of objects: [{"time": 12.5, "text": "Verse 1 line"}]'
    )
    writer_credit = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lyrics: {self.song.title}"


class SongContributor(models.Model):
    """
    Musicians, producers, lyricists, mixers, and featured artists credited on the track.
    """
    ROLE_CHOICES = (
        ('featured_artist', 'Featured Vocalist / Artist'),
        ('producer', 'Music Producer'),
        ('composer', 'Composer / Songwriter'),
        ('lyricist', 'Lyricist'),
        ('mix_engineer', 'Mix Engineer'),
        ('mastering_engineer', 'Mastering Engineer'),
        ('session_musician', 'Session Instrumentalist'),
    )
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='contributors')
    artist = models.ForeignKey('artists.Artist', on_delete=models.SET_NULL, null=True, blank=True, related_name='credited_tracks')
    name = models.CharField(max_length=150, help_text='Contributor stage or legal name')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='producer')
    instrument = models.CharField(max_length=100, blank=True, help_text='e.g., Electric Guitar, Synthesizer')
    royalty_split_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) on {self.song.title}"


class TrackRating(models.Model):
    """
    User 1-5 star ratings for audio tracks.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='track_ratings')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='ratings')
    stars = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'song')

    def __str__(self):
        return f"{self.user.username} rated {self.song.title} ({self.stars} stars)"


class TrackComment(models.Model):
    """
    Timestamped song discussions and feedback from listeners.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='track_comments')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='comments')
    comment_text = models.TextField(max_length=1000)
    timestamp_seconds = models.FloatField(null=True, blank=True, help_text='Optional audio timestamp where comment is pinned')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_flagged = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} on {self.song.title}: {self.comment_text[:40]}"
