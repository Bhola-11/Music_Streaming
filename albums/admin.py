"""
Admin Configuration for Albums & Discographies.
"""
from django.contrib import admin
from .models import Album, AlbumTrack, DiscEdition, AlbumReview, RecordLabel


class AlbumTrackInline(admin.TabularInline):
    model = AlbumTrack
    extra = 1
    raw_id_fields = ('song',)


class DiscEditionInline(admin.TabularInline):
    model = DiscEdition
    extra = 0


@admin.register(RecordLabel)
class RecordLabelAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'website')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'album_type', 'record_label', 'release_date', 'is_published')
    list_filter = ('album_type', 'is_published', 'release_date')
    search_fields = ('title', 'artist__name', 'upc_code')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (AlbumTrackInline, DiscEditionInline)


@admin.register(AlbumReview)
class AlbumReviewAdmin(admin.ModelAdmin):
    list_display = ('album', 'user', 'rating', 'title', 'created_at')
    list_filter = ('rating', 'created_at')
