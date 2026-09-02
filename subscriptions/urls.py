from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', views.PricingPlansView.as_view(), name='plans'),
]
