"""
Django Admin Configuration for Accounts & Security models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User,
    UserProfile,
    UserPreferences,
    TwoFactorAuth,
    SecurityQuestion,
    UserSession,
    UserFollow,
    ArtistProfileLink,
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserPreferencesInline(admin.StackedInline):
    model = UserPreferences
    can_delete = False
    verbose_name_plural = 'Preferences'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for Custom User Model.
    """
    inlines = (UserProfileInline, UserPreferencesInline)
    list_display = ('username', 'email', 'role', 'is_premium', 'is_verified', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_premium', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'first_name', 'last_name', 'phone', 'avatar')}),
        (_('MusicVerse Tier & Quota'), {'fields': ('role', 'is_premium', 'premium_expires_at', 'storage_quota_bytes', 'storage_used_bytes')}),
        (_('Security Status'), {'fields': ('is_verified', 'is_locked', 'lock_expires_at', 'failed_login_attempts', 'last_login_ip')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'role', 'password', 'password_confirm'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'country', 'is_public', 'updated_at')
    search_fields = ('user__username', 'user__email', 'bio', 'location')


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    list_display = ('user', 'audio_quality', 'visualizer_mode', 'equalizer_preset', 'theme')
    list_filter = ('audio_quality', 'visualizer_mode', 'theme')


@admin.register(TwoFactorAuth)
class TwoFactorAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_enabled', 'last_used_at', 'created_at')
    list_filter = ('is_enabled',)


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_type', 'ip_address', 'location_city', 'is_active', 'last_activity')
    list_filter = ('is_active', 'device_type')
    search_fields = ('user__email', 'ip_address', 'device_type')


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')


@admin.register(ArtistProfileLink)
class ArtistProfileLinkAdmin(admin.ModelAdmin):
    list_display = ('user', 'artist', 'role', 'can_upload_music', 'can_manage_releases')
    list_filter = ('role',)
