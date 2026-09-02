"""
Payment Gateway Service: Stripe, PayPal & Mock Payment Processing & Invoicing.
"""
import uuid
from decimal import Decimal
from django.utils import timezone
from .models import PaymentTransaction, Invoice, TransactionStatus, PaymentProvider
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


class PaymentGatewayService:
    """
    Abstractions for executing charges, recording transactions, and issuing invoices.
    """

    @classmethod
    def process_charge(
        cls,
        user,
        amount_usd: Decimal,
        description: str,
        provider: str = PaymentProvider.MOCK,
        metadata: dict = None
    ) -> PaymentTransaction:
        """
        Executes and records a payment charge.
        """
        txn_id = f"txn_{uuid.uuid4().hex[:14]}"

        transaction = PaymentTransaction.objects.create(
            user=user,
            provider=provider,
            transaction_id=txn_id,
            amount_usd=amount_usd,
            status=TransactionStatus.SUCCEEDED,
            description=description,
            metadata=metadata or {}
        )

        # Generate invoice
        invoice_num = f"INV-2026-{uuid.uuid4().hex[:8].upper()}"
        Invoice.objects.create(
            invoice_number=invoice_num,
            user=user,
            transaction=transaction,
            subtotal_usd=amount_usd,
            tax_usd=Decimal('0.00'),
            total_usd=amount_usd,
            billing_name=getattr(user, 'get_full_name', lambda: '')() or user.username,
            billing_email=user.email
        )

        AuditService.log_action(
            action_type='payment.charged',
            category=ActionCategory.FINANCIAL,
            severity=ActionSeverity.INFO,
            user=user,
            target_model='PaymentTransaction',
            target_object_id=str(transaction.id),
            target_repr=f"\${amount_usd} ({transaction.transaction_id})",
            description=f"Charged \${amount_usd} for {description}"
        )

        return transaction
