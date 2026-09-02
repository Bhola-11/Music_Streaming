from django.apps import AppConfig
from django.db import models
from django.conf import settings
import uuid


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'
    verbose_name = 'Subscriptions & Tiers'


class SubscriptionPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    price_usd_monthly = models.DecimalField(max_digits=6, decimal_places=2, default=9.99)
    price_usd_yearly = models.DecimalField(max_digits=6, decimal_places=2, default=99.99)
    features_list = models.JSONField(default=list)
    has_lossless_audio = models.BooleanField(default=True)
    has_unlimited_skips = models.BooleanField(default=True)
    has_offline_downloads = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (${self.price_usd_monthly}/mo)"


class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, related_name='subscribers')
    is_active = models.BooleanField(default=False)
    starts_at = models.DateTimeField(auto_now_add=True)
    renews_at = models.DateTimeField(null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=150, blank=True)
