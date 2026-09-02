"""
Admin Configuration for Platform Analytics.
"""
from django.contrib import admin
from .models import DailyPlatformMetric, StreamGeoHeatmap, SuspiciousActivityFlag


@admin.register(DailyPlatformMetric)
class DailyPlatformMetricAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_streams', 'unique_listeners', 'bandwidth_served_gb', 'royalty_accrued_usd')


@admin.register(StreamGeoHeatmap)
class StreamGeoHeatmapAdmin(admin.ModelAdmin):
    list_display = ('country_name', 'country_code', 'stream_count', 'listener_count')


@admin.register(SuspiciousActivityFlag)
class SuspiciousActivityFlagAdmin(admin.ModelAdmin):
    list_display = ('flag_reason', 'ip_address', 'stream_burst_count', 'is_blocked', 'flagged_at')
    list_filter = ('is_blocked', 'flagged_at')
