from django.urls import path
from . import views

app_name = 'discovery'

urlpatterns = [
    path('', views.DiscoveryHubView.as_view(), name='hub'),
    path('search/', views.SearchGlobalView.as_view(), name='search'),
]
