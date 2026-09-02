"""
Payment Processing Models: Gateway Transactions, Invoices,
Payment Methods, and Webhook Audit Trails.
"""
import uuid
from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils import timezone


class PaymentProvider(models.TextChoices):
    STRIPE = 'stripe', 'Stripe Payments'
    PAYPAL = 'paypal', 'PayPal Gateway'
    MOCK = 'mock', 'Test / Mock Sandbox'


class TransactionStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SUCCEEDED = 'succeeded', 'Succeeded'
    FAILED = 'failed', 'Failed'
    REFUNDED = 'refunded', 'Refunded'


class PaymentTransaction(models.Model):
    """
    Immutable ledger of payment attempts, subscriptions charges, and refunds.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    provider = models.CharField(max_length=20, choices=PaymentProvider.choices, default=PaymentProvider.STRIPE)
    transaction_id = models.CharField(max_length=150, unique=True, db_index=True, default=uuid.uuid4)
    
    amount_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=TransactionStatus.choices, default=TransactionStatus.PENDING, db_index=True)
    currency = models.CharField(max_length=5, default='USD')
    description = models.CharField(max_length=255, blank=True, default='')
    
    idempotency_key = models.CharField(max_length=100, blank=True, db_index=True)
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.status.upper()}] \${self.amount_usd} by {self.user.username} ({self.transaction_id})"


class Invoice(models.Model):
    """
    Tax compliant digital invoice generated after successful billing transactions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='invoice')
    
    subtotal_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    tax_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    
    billing_name = models.CharField(max_length=150, blank=True, default='')
    billing_email = models.EmailField(blank=True, default='')
    billing_country = models.CharField(max_length=100, default='United States')
    
    issued_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} (\${self.total_usd})"


class BillingAddress(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='billing_address')
    full_name = models.CharField(max_length=150)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Billing address for {self.user.username}"
