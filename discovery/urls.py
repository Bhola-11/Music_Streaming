"""
URL Routing for Discovery, Global Search & Music Charts.
"""
from django.urls import path
from . import views

app_name = 'discovery'

urlpatterns = [
    path('', views.DiscoveryHubView.as_view(), name='hub'),
    path('search/', views.GlobalSearchView.as_view(), name='search'),
    path('charts/', views.TrendingChartsView.as_view(), name='charts'),
    path('charts/<slug:slug>/', views.ChartDetailView.as_view(), name='chart_detail'),
]
