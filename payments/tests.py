"""
Phase 4 Test Suite — Payments: Gateway Processing, Invoices & Webhooks.
"""
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import PaymentTransaction, Invoice, TransactionStatus, PaymentProvider
from .services import PaymentGatewayService
from subscriptions.models import SubscriptionTier

User = get_user_model()


class PaymentProcessingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(email='pay_u@mv.io', username='pay_u', password='pass12345')
        self.tier = SubscriptionTier.objects.create(
            name='Studio Master',
            slug='studio-master',
            price_monthly_usd=19.99
        )

    def test_process_charge_service(self):
        txn = PaymentGatewayService.process_charge(
            user=self.user,
            amount_usd=Decimal('19.99'),
            description='Studio Master Plan'
        )
        self.assertEqual(txn.status, TransactionStatus.SUCCEEDED)
        self.assertEqual(Invoice.objects.filter(user=self.user).count(), 1)

    def test_checkout_view(self):
        self.client.login(email='pay_u@mv.io', password='pass12345')
        url = reverse('payments:checkout', args=[self.tier.slug])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Studio Master')

    def test_stripe_webhook_api(self):
        url = reverse('payments:stripe_webhook')
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
