"""
Views for Subscription Plans Showcase, Plan Selection, and Subscription Management.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

from .models import SubscriptionTier, UserSubscription, SubscriptionStatus, BillingCycle
from audit.services import AuditService
from audit.models import ActionCategory


class SubscriptionPlansView(ListView):
    """
    Public pricing table showing all tiers and audio quality privileges.
    """
    model = SubscriptionTier
    template_name = 'subscriptions/plans.html'
    context_object_name = 'tiers'

    def get_queryset(self):
        return SubscriptionTier.objects.filter(is_active=True).prefetch_related('benefits')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['current_subscription'] = getattr(self.request.user, 'active_subscription', None)
        return context


class MySubscriptionView(LoginRequiredMixin, TemplateView):
    """
    User subscription management portal.
    """
    template_name = 'subscriptions/my_subscription.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subscription'] = getattr(self.request.user, 'active_subscription', None)
        return context


class SubscribePlanCheckoutView(LoginRequiredMixin, View):
    """
    Subscribes user to a tier (or redirects to payment processing).
    """
    def post(self, request, tier_slug):
        tier = get_object_or_404(SubscriptionTier, slug=tier_slug, is_active=True)
        cycle = request.POST.get('billing_cycle', BillingCycle.MONTHLY)

        # 30 days period
        period_days = 365 if cycle == BillingCycle.ANNUAL else 30
        end_date = timezone.now() + timedelta(days=period_days)

        sub, created = UserSubscription.objects.update_or_create(
            user=request.user,
            defaults={
                'tier': tier,
                'status': SubscriptionStatus.ACTIVE,
                'billing_cycle': cycle,
                'current_period_start': timezone.now(),
                'current_period_end': end_date,
                'cancel_at_period_end': False,
            }
        )

        AuditService.log_action(
            action_type='subscription.activated',
            category=ActionCategory.FINANCIAL,
            user=request.user,
            target_model='UserSubscription',
            target_object_id=str(sub.id),
            description=f"User subscribed to {tier.name} ({cycle})"
        )

        messages.success(request, f"Welcome to {tier.name}! Hi-Fi Master streaming is now unlocked.")
        return redirect('subscriptions:my_subscription')


class CancelSubscriptionView(LoginRequiredMixin, View):
    """
    Cancels subscription at the end of the billing period.
    """
    def post(self, request):
        sub = getattr(request.user, 'active_subscription', None)
        if sub:
            sub.cancel_at_period_end = True
            sub.canceled_at = timezone.now()
            sub.save(update_fields=['cancel_at_period_end', 'canceled_at'])

            AuditService.log_action(
                action_type='subscription.canceled',
                category=ActionCategory.FINANCIAL,
                user=request.user,
                description=f"User scheduled subscription cancellation for {sub.tier.name}"
            )
            messages.info(request, "Your subscription has been canceled and will expire at the end of your billing cycle.")
        return redirect('subscriptions:my_subscription')
