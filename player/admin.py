"""
Admin Configuration for Player Queues, Listening History, and Sessions.
"""
from django.contrib import admin
from .models import PlaybackSession, PlaybackQueue, QueueItem, ListeningHistory, FavoriteTrack, RadioStation


class QueueItemInline(admin.TabularInline):
    model = QueueItem
    extra = 1
    raw_id_fields = ('song',)


@admin.register(PlaybackSession)
class PlaybackSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_song', 'is_playing', 'progress_seconds', 'volume_percent', 'active_device_name', 'last_ping')
    search_fields = ('user__username', 'current_song__title')


@admin.register(PlaybackQueue)
class PlaybackQueueAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    inlines = (QueueItemInline,)


@admin.register(ListeningHistory)
class ListeningHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'seconds_played', 'completion_percentage', 'was_skipped', 'played_at')
    list_filter = ('was_skipped', 'played_at')
    search_fields = ('user__username', 'song__title')


@admin.register(FavoriteTrack)
class FavoriteTrackAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'created_at')
    search_fields = ('user__username', 'song__title')
