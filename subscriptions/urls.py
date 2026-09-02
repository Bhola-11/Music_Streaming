"""
URL Routing for Subscriptions & Pricing Plans.
"""
from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', views.SubscriptionPlansView.as_view(), name='plans'),
    path('me/', views.MySubscriptionView.as_view(), name='my_subscription'),
    path('subscribe/<slug:tier_slug>/', views.SubscribePlanCheckoutView.as_view(), name='subscribe'),
    path('cancel/', views.CancelSubscriptionView.as_view(), name='cancel'),
]
