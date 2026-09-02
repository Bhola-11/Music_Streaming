"""
Admin Configuration for Payment Transactions and Invoices.
"""
from django.contrib import admin
from .models import PaymentTransaction, Invoice, BillingAddress


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount_usd', 'status', 'provider', 'created_at')
    list_filter = ('status', 'provider', 'created_at')
    search_fields = ('transaction_id', 'user__username', 'description')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user', 'total_usd', 'issued_at')
    search_fields = ('invoice_number', 'user__username', 'billing_name')
