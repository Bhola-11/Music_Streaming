"""
Playlist System Models: Personal Playlists, Collaborative Curation,
Track Sequencing, Tags, and Social Following.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class PlaylistPrivacy(models.TextChoices):
    PUBLIC = 'public', 'Public (Discoverable by Everyone)'
    UNLISTED = 'unlisted', 'Unlisted (Only with Link)'
    PRIVATE = 'private', 'Private (Only Creator & Collaborators)'


class CollaboratorRole(models.TextChoices):
    VIEWER = 'viewer', 'Can View Only'
    EDITOR = 'editor', 'Can Add & Remove Tracks'
    ADMIN = 'admin', 'Can Manage Settings & Collaborators'


class Playlist(models.Model):
    """
    User curated collection of songs with collaborative and privacy controls.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_playlists', null=True, blank=True)
    title = models.CharField(max_length=150, db_index=True)
    slug = models.SlugField(max_length=180, db_index=True)
    description = models.TextField(blank=True, max_length=1000)
    cover_image = models.ImageField(upload_to='covers/playlists/%Y/%m/', blank=True, null=True)
    
    privacy = models.CharField(
        max_length=20,
        choices=PlaylistPrivacy.choices,
        default=PlaylistPrivacy.PUBLIC,
        db_index=True
    )
    is_collaborative = models.BooleanField(default=False, help_text='Allow invited users to add tracks')
    is_featured_curated = models.BooleanField(default=False, help_text='Featured on homepage by editorial team')
    
    # Metrics
    follower_count = models.PositiveIntegerField(default=0, db_index=True)
    play_count = models.PositiveBigIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'privacy']),
            models.Index(fields=['is_featured_curated', '-follower_count']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'playlist'
            self.slug = f"{base_slug}-{str(self.id)[:6]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (by {self.owner.username})"

    @property
    def cover_art_url(self):
        if self.cover_image and hasattr(self.cover_image, 'url'):
            return self.cover_image.url
        # Fallback to first track's cover or default gradient image
        first_track = self.playlist_tracks.select_related('song').first()
        if first_track and first_track.song.cover_art_url:
            return first_track.song.cover_art_url
        return 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=400&auto=format&fit=crop&q=80'

    @property
    def total_duration_seconds(self):
        return sum(pt.song.duration_seconds for pt in self.playlist_tracks.select_related('song') if pt.song)

    @property
    def formatted_total_duration(self):
        total = self.total_duration_seconds
        mins = total // 60
        hrs = mins // 60
        rem_mins = mins % 60
        if hrs > 0:
            return f"{hrs} hr {rem_mins} min"
        return f"{rem_mins} min"


class PlaylistTrack(models.Model):
    """
    Junction table representing an ordered song entry in a playlist.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='playlist_tracks')
    song = models.ForeignKey('music.Song', on_delete=models.CASCADE, related_name='playlist_entries')
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.PositiveIntegerField(default=1, db_index=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'added_at']
        unique_together = ('playlist', 'song')

    def __str__(self):
        return f"#{self.position} {self.song.title} in {self.playlist.title}"


class PlaylistCollaborator(models.Model):
    """
    Invited collaborator permissions on a shared playlist.
    """
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='collaborators')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='collaborating_playlists')
    role = models.CharField(max_length=20, choices=CollaboratorRole.choices, default=CollaboratorRole.EDITOR)
    invited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('playlist', 'user')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()}) on {self.playlist.title}"


class PlaylistFollower(models.Model):
    """
    Social bookmarking/following of public playlists.
    """
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='followers')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followed_playlists')
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('playlist', 'user')

    def __str__(self):
        return f"{self.user.username} follows {self.playlist.title}"
