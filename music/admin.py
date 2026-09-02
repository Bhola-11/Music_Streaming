"""
Admin configuration for Music models.
"""
from django.contrib import admin
from .models import Genre, Mood, Song, SongFile, Lyrics, SongContributor, TrackRating, TrackComment


class SongFileInline(admin.TabularInline):
    model = SongFile
    extra = 1


class LyricsInline(admin.StackedInline):
    model = Lyrics
    extra = 0


class SongContributorInline(admin.TabularInline):
    model = SongContributor
    extra = 1


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color_hex', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Mood)
class MoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'genre', 'duration_seconds', 'bitrate_kbps', 'is_premium_only', 'play_count', 'is_published')
    list_filter = ('is_published', 'is_premium_only', 'is_explicit', 'genre')
    search_fields = ('title', 'artist__name', 'isrc_code')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (SongFileInline, LyricsInline, SongContributorInline)


@admin.register(TrackComment)
class TrackCommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'timestamp_seconds', 'created_at', 'is_flagged')
    list_filter = ('is_flagged', 'created_at')
    search_fields = ('user__username', 'song__title', 'comment_text')


@admin.register(TrackRating)
class TrackRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'stars', 'created_at')
    list_filter = ('stars',)
