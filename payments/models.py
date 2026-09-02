from django.apps import AppConfig
from django.db import models
from django.conf import settings
import uuid


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'


class PaymentTransaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payments')
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    gateway = models.CharField(max_length=50, default='stripe')  # stripe, paypal, razorpay
    status = models.CharField(max_length=30, default='completed')  # pending, completed, failed, refunded
    transaction_reference = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='invoices')
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    pdf_file = models.FileField(upload_to='invoices/%Y/%m/', blank=True, null=True)
    issued_date = models.DateField(auto_now_add=True)
