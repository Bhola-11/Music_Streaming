"""
URL Routing for Player Engine, Queues, Favorites, History & Radio.
"""
from django.urls import path
from . import views

app_name = 'player'

urlpatterns = [
    # User Collections
    path('favorites/', views.FavoritesListView.as_view(), name='favorites'),
    path('history/', views.ListeningHistoryListView.as_view(), name='history'),

    # JSON APIs
    path('api/favorite/<uuid:pk>/', views.ToggleFavoriteTrackAPIView.as_view(), name='api_toggle_favorite'),
    path('api/history/<uuid:pk>/', views.RecordPlaybackHistoryAPIView.as_view(), name='api_record_history'),
    path('api/queue/', views.GetActiveQueueAPIView.as_view(), name='api_get_queue'),
    path('api/queue/add/<uuid:pk>/', views.QueueAddAPIView.as_view(), name='api_queue_add'),
    path('api/queue/remove/<uuid:item_id>/', views.QueueRemoveAPIView.as_view(), name='api_queue_remove'),
    path('api/queue/clear/', views.QueueClearAPIView.as_view(), name='api_queue_clear'),
    path('api/radio/<uuid:pk>/', views.StartRadioFromSongAPIView.as_view(), name='api_start_radio'),
]
