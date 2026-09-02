import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Playlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_playlists')
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='covers/playlists/%Y/%m/', blank=True, null=True)
    is_public = models.BooleanField(default=True)
    is_collaborative = models.BooleanField(default=False)
    follower_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.creator.username}-{self.title}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='playlist_items')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='playlist_entries')
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'added_at']
        unique_together = ('playlist', 'song')
