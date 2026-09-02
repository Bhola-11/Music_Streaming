"""
Admin Configuration for Discovery, Banners & Charts.
"""
from django.contrib import admin
from .models import FeaturedBanner, MusicChart, ChartEntry, TrendingMetric, SearchQueryLog


class ChartEntryInline(admin.TabularInline):
    model = ChartEntry
    extra = 1
    raw_id_fields = ('song',)


@admin.register(FeaturedBanner)
class FeaturedBannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge_text', 'display_order', 'is_active', 'created_at')
    list_editable = ('display_order', 'is_active')


@admin.register(MusicChart)
class MusicChartAdmin(admin.ModelAdmin):
    list_display = ('title', 'chart_type', 'is_published', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = (ChartEntryInline,)


@admin.register(SearchQueryLog)
class SearchQueryLogAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'user', 'results_count', 'created_at')
    search_fields = ('query_text', 'user__username')
