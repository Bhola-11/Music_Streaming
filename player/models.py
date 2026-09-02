"""
Player Architecture Models: Playback Queues, Listening History,
Favorite Tracks, Device Playback Sessions, and Smart Radio Stations.
"""
import uuid
from django.db import models
from django.conf import settings


class RepeatMode(models.TextChoices):
    OFF = 'off', 'Repeat Off'
    ALL = 'all', 'Repeat All Queue'
    ONE = 'one', 'Repeat Single Track'


class PlaybackSession(models.Model):
    """
    Active player state per user across devices (web browser, mobile, desktop).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playback_session')
    current_song = models.ForeignKey('music.Song', on_delete=models.SET_NULL, null=True, blank=True)
    progress_seconds = models.PositiveIntegerField(default=0)
    is_playing = models.BooleanField(default=False)
    is_shuffled = models.BooleanField(default=False)
    repeat_mode = models.CharField(max_length=10, choices=RepeatMode.choices, default=RepeatMode.OFF)
    volume_percent = models.PositiveSmallIntegerField(default=80)
    active_device_name = models.CharField(max_length=100, default='Web Browser')
    last_ping = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session for {self.user.username} ({'Playing' if self.is_playing else 'Paused'})"


class PlaybackQueue(models.Model):
    """
    Current up-next audio playback queue for the user.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='playback_queue')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Queue for {self.user.username}"


class QueueItem(models.Model):
    """
    A single track entry within the active playback queue.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    queue = models.ForeignKey(PlaybackQueue, on_delete=models.CASCADE, related_name='items')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE)
    position = models.PositiveIntegerField(default=1, db_index=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'added_at']

    def __str__(self):
        return f"#{self.position} - {self.song.title}"


class ListeningHistory(models.Model):
    """
    Detailed audit log of user streams, listening duration, completion rates, and device specs.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listening_history')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='stream_logs')
    seconds_played = models.PositiveIntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)
    was_skipped = models.BooleanField(default=False)
    device_info = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    played_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-played_at']
        indexes = [
            models.Index(fields=['user', '-played_at']),
            models.Index(fields=['song', '-played_at']),
        ]

    def __str__(self):
        return f"{self.user.username} streamed {self.song.title} ({self.completion_percentage:.0f}%)"


class FavoriteTrack(models.Model):
    """
    User's 'Liked Songs' library.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_tracks')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'song')

    def __str__(self):
        return f"{self.user.username} ❤️ {self.song.title}"


class RadioStation(models.Model):
    """
    Dynamic infinite radio based on a seed song, artist, or genre.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    seed_song = models.ForeignKey('music.Song', on_delete=models.CASCADE, null=True, blank=True)
    seed_artist = models.ForeignKey('artists.Artist', on_delete=models.CASCADE, null=True, blank=True)
    seed_genre = models.ForeignKey('music.Genre', on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Radio: {self.title}"
