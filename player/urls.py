from django.urls import path
from . import views

app_name = 'player'

urlpatterns = [
    path('sync-state/', views.SyncPlaybackStateView.as_view(), name='sync_state'),
]
