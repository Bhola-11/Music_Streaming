"""
Admin Configuration for Recommendations.
"""
from django.contrib import admin
from .models import UserTasteProfile, TrackSimilarity, DailyMix, DailyMixTrack, RecommendationHistory


class DailyMixTrackInline(admin.TabularInline):
    model = DailyMixTrack
    extra = 1
    raw_id_fields = ('song',)


@admin.register(UserTasteProfile)
class UserTasteProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'diversity_score', 'updated_at')


@admin.register(DailyMix)
class DailyMixAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'mix_number', 'generated_at')
    inlines = (DailyMixTrackInline,)


@admin.register(TrackSimilarity)
class TrackSimilarityAdmin(admin.ModelAdmin):
    list_display = ('source_song', 'target_song', 'similarity_score')
