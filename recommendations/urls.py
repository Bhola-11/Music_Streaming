"""
URL Routing for Algorithmic Recommendations.
"""
from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('made-for-you/', views.MadeForYouFeedView.as_view(), name='feed'),
    path('mix/<uuid:pk>/', views.DailyMixDetailView.as_view(), name='daily_mix'),
    path('api/similar/<uuid:pk>/', views.SimilarTracksAPIView.as_view(), name='api_similar'),
]
