"""
Admin Configuration for Content Moderation.
"""
from django.contrib import admin
from .models import ModerationReport, TakedownRequest, ContentFilterRule


@admin.register(ModerationReport)
class ModerationReportAdmin(admin.ModelAdmin):
    list_display = ('reason', 'status', 'reporter', 'song', 'artist', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('description', 'reporter__username', 'song__title')


@admin.register(TakedownRequest)
class TakedownRequestAdmin(admin.ModelAdmin):
    list_display = ('claimant_name', 'copyright_owner', 'infringing_song', 'status', 'submitted_at')
    list_filter = ('status', 'submitted_at')


@admin.register(ContentFilterRule)
class ContentFilterRuleAdmin(admin.ModelAdmin):
    list_display = ('keyword_pattern', 'severity_level', 'auto_quarantine', 'created_at')
