"""
Subscription System Models: Tiers, User Subscriptions, Plan Benefits & Promotional Coupons.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class BillingCycle(models.TextChoices):
    MONTHLY = 'monthly', 'Monthly'
    ANNUAL = 'annual', 'Annual (Save 20%)'


class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    TRIALING = 'trialing', 'In Free Trial'
    PAST_DUE = 'past_due', 'Past Due'
    CANCELED = 'canceled', 'Canceled'
    EXPIRED = 'expired', 'Expired'


class SubscriptionTier(models.Model):
    """
    Tier definitions (Free Listener, Hi-Fi Pro, Creator Master, Family Plan).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    price_monthly_usd = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    price_annual_usd = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    
    # Feature flags
    allows_lossless = models.BooleanField(default=False, help_text='Unlocks 1411kbps FLAC streaming')
    allows_offline = models.BooleanField(default=False)
    allows_artist_studio = models.BooleanField(default=False)
    allows_stems_download = models.BooleanField(default=False)
    max_devices = models.PositiveSmallIntegerField(default=1)
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.name} (\${self.price_monthly_usd}/mo)"


class SubscriptionBenefit(models.Model):
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.CASCADE, related_name='benefits')
    benefit_text = models.CharField(max_length=200)
    display_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f"{self.tier.name}: {self.benefit_text}"


class UserSubscription(models.Model):
    """
    User's active subscription contract.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='active_subscription')
    tier = models.ForeignKey(SubscriptionTier, on_delete=models.PROTECT, related_name='subscribers', null=True, blank=True)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.ACTIVE)
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices, default=BillingCycle.MONTHLY)
    
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(default=timezone.now)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # Payment Provider Reference
    payment_customer_id = models.CharField(max_length=150, blank=True)
    payment_subscription_id = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} -> {self.tier.name} ({self.status})"

    @property
    def is_valid(self):
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING] and self.current_period_end > timezone.now()


class PromoCoupon(models.Model):
    """
    Discount promotional coupon codes.
    """
    code = models.CharField(max_length=30, unique=True)
    discount_percent = models.PositiveSmallIntegerField(default=20)
    max_uses = models.PositiveIntegerField(default=500)
    times_used = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} ({self.discount_percent}% off)"

    @property
    def is_usable(self):
        return self.is_active and self.times_used < self.max_uses and self.expires_at > timezone.now()
