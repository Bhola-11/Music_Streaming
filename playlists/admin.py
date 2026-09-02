"""
Admin Configuration for Playlists, Collaborators & Tracks.
"""
from django.contrib import admin
from .models import Playlist, PlaylistTrack, PlaylistCollaborator, PlaylistFollower


class PlaylistTrackInline(admin.TabularInline):
    model = PlaylistTrack
    extra = 1
    raw_id_fields = ('song',)


class PlaylistCollaboratorInline(admin.TabularInline):
    model = PlaylistCollaborator
    extra = 0


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'privacy', 'is_collaborative', 'is_featured_curated', 'follower_count', 'created_at')
    list_filter = ('privacy', 'is_collaborative', 'is_featured_curated')
    search_fields = ('title', 'owner__username', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (PlaylistTrackInline, PlaylistCollaboratorInline)


@admin.register(PlaylistFollower)
class PlaylistFollowerAdmin(admin.ModelAdmin):
    list_display = ('user', 'playlist', 'followed_at')
    search_fields = ('user__username', 'playlist__title')
