"""
URL Routing for Payments, Invoices & Checkout.
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<slug:tier_slug>/', views.CheckoutView.as_view(), name='checkout'),
    path('success/<str:txn_id>/', views.PaymentSuccessView.as_view(), name='success'),
    path('invoice/<str:invoice_number>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('webhook/stripe/', views.StripeWebhookAPIView.as_view(), name='stripe_webhook'),
]
