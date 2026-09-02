"""
Phase 4 Test Suite — Subscriptions: Tiers, Privileges & Lifecycle Management.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from .models import SubscriptionTier, UserSubscription, SubscriptionStatus, BillingCycle

User = get_user_model()


class SubscriptionLifecycleTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='sub_u@mv.io', username='sub_u', password='pass12345')
        self.tier = SubscriptionTier.objects.create(
            name='Hi-Fi Pro',
            slug='hi-fi-pro',
            price_monthly_usd=9.99,
            price_annual_usd=99.99,
            allows_lossless=True
        )

    def test_plans_view(self):
        url = reverse('subscriptions:plans')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Hi-Fi Pro')

    def test_subscribe_flow(self):
        self.client.login(email='sub_u@mv.io', password='pass12345')
        url = reverse('subscriptions:subscribe', args=[self.tier.slug])
        res = self.client.post(url, {'billing_cycle': BillingCycle.MONTHLY})
        self.assertEqual(res.status_code, 302)

        sub = UserSubscription.objects.get(user=self.user)
        self.assertEqual(sub.tier, self.tier)
        self.assertTrue(sub.is_valid)

    def test_cancel_subscription(self):
        self.client.login(email='sub_u@mv.io', password='pass12345')
        sub = UserSubscription.objects.create(
            user=self.user,
            tier=self.tier,
            status=SubscriptionStatus.ACTIVE,
            current_period_end=timezone.now() + timedelta(days=30)
        )
        url = reverse('subscriptions:cancel')
        self.client.post(url)
        sub.refresh_from_db()
        self.assertTrue(sub.cancel_at_period_end)
