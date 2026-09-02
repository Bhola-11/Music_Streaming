import uuid
from django.db import models
from django.conf import settings


class ListeningHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listening_history')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='play_history')
    played_at = models.DateTimeField(auto_now_add=True, db_index=True)
    duration_played_seconds = models.PositiveIntegerField(default=0)
    completed_stream = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-played_at']
        verbose_name_plural = 'Listening histories'


class LikedSong(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='liked_songs')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ('user', 'song')
        ordering = ['-created_at']


class UserQueue(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='player_queue')
    current_song = models.ForeignKey('music.Song', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    queue_song_ids = models.JSONField(default=list, blank=True)
    playback_position_ms = models.PositiveIntegerField(default=0)
    is_playing = models.BooleanField(default=False)
    shuffle_mode = models.BooleanField(default=False)
    repeat_mode = models.CharField(max_length=10, default='off')  # off, one, all
    updated_at = models.DateTimeField(auto_now=True)
