"""
URL Routing for Analytics & Telemetry Dashboards.
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.PlatformAnalyticsDashboardView.as_view(), name='dashboard'),
    path('artist/', views.ArtistAnalyticsDeepDiveView.as_view(), name='artist_analytics'),
    path('api/realtime/', views.RealtimeMetricsAPIView.as_view(), name='realtime_api'),
]
