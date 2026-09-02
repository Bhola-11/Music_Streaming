"""
Admin Configuration for Artists, Verification Requests, and Royalty Statements.
"""
from django.contrib import admin
from .models import Artist, ArtistMember, ArtistVerificationRequest, PayoutAccount, RoyaltyStatement, ArtistFollower


class ArtistMemberInline(admin.TabularInline):
    model = ArtistMember
    extra = 1


class PayoutAccountInline(admin.StackedInline):
    model = PayoutAccount
    extra = 0


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'verification_status', 'monthly_listeners', 'total_streams', 'unpaid_balance')
    list_filter = ('verification_status', 'country_of_origin', 'created_at')
    search_fields = ('name', 'stage_name', 'user__email')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (ArtistMemberInline, PayoutAccountInline)


@admin.register(ArtistVerificationRequest)
class ArtistVerificationRequestAdmin(admin.ModelAdmin):
    list_display = ('artist', 'legal_name', 'status', 'submitted_at', 'reviewed_by')
    list_filter = ('status', 'submitted_at')
    search_fields = ('artist__name', 'legal_name')


@admin.register(RoyaltyStatement)
class RoyaltyStatementAdmin(admin.ModelAdmin):
    list_display = ('artist', 'period_start', 'total_streams', 'gross_earnings_usd', 'net_payable_usd', 'is_paid')
    list_filter = ('is_paid', 'period_start')
    search_fields = ('artist__name',)


@admin.register(ArtistFollower)
class ArtistFollowerAdmin(admin.ModelAdmin):
    list_display = ('user', 'artist', 'created_at')
    search_fields = ('user__username', 'artist__name')
