"""
Admin Configuration for Subscriptions, Tiers & Coupons.
"""
from django.contrib import admin
from .models import SubscriptionTier, SubscriptionBenefit, UserSubscription, PromoCoupon


class SubscriptionBenefitInline(admin.TabularInline):
    model = SubscriptionBenefit
    extra = 2


@admin.register(SubscriptionTier)
class SubscriptionTierAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_monthly_usd', 'price_annual_usd', 'allows_lossless', 'is_popular', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    inlines = (SubscriptionBenefitInline,)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tier', 'status', 'billing_cycle', 'current_period_end', 'cancel_at_period_end')
    list_filter = ('status', 'billing_cycle', 'tier')
    search_fields = ('user__username', 'user__email')


@admin.register(PromoCoupon)
class PromoCouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'times_used', 'max_uses', 'expires_at', 'is_active')
