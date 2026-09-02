from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import SubscriptionPlan

class PricingPlansView(ListView):
    model = SubscriptionPlan
    template_name = 'subscriptions/plans.html'
    context_object_name = 'plans'
