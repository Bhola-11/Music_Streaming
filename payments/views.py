"""
Payment Views: Checkout Portal, Invoices, Payment History, and Webhook Receivers.
"""
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import PaymentTransaction, Invoice, BillingAddress, PaymentProvider
from .services import PaymentGatewayService
from subscriptions.models import SubscriptionTier


class CheckoutView(LoginRequiredMixin, View):
    """
    Checkout page for reviewing tier pricing, tax calculation, and payment method.
    """
    template_name = 'payments/checkout.html'

    def get(self, request, tier_slug):
        tier = get_object_or_404(SubscriptionTier, slug=tier_slug, is_active=True)
        cycle = request.GET.get('cycle', 'monthly')
        price = tier.price_annual_usd if cycle == 'annual' else tier.price_monthly_usd
        return render(request, self.template_name, {
            'tier': tier,
            'cycle': cycle,
            'price': price,
        })

    def post(self, request, tier_slug):
        tier = get_object_or_404(SubscriptionTier, slug=tier_slug, is_active=True)
        cycle = request.POST.get('cycle', 'monthly')
        price = tier.price_annual_usd if cycle == 'annual' else tier.price_monthly_usd

        # Process charge
        txn = PaymentGatewayService.process_charge(
            user=request.user,
            amount_usd=price,
            description=f"Subscription to {tier.name} ({cycle})",
            provider=PaymentProvider.MOCK
        )

        # Trigger subscription update
        return redirect('payments:success', txn_id=txn.transaction_id)


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        txn_id = self.kwargs.get('txn_id')
        context['transaction'] = get_object_or_404(PaymentTransaction, transaction_id=txn_id, user=self.request.user)
        context['invoice'] = getattr(context['transaction'], 'invoice', None)
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    """
    Digital printable invoice.
    """
    model = Invoice
    template_name = 'payments/invoice.html'
    slug_field = 'invoice_number'
    slug_url_kwarg = 'invoice_number'
    context_object_name = 'invoice'

    def get_queryset(self):
        return Invoice.objects.filter(user=self.request.user)


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookAPIView(View):
    """
    Mock/live webhook receiver for asynchronous payment confirmations.
    """
    def post(self, request):
        return JsonResponse({'received': True, 'status': 'processed'})
