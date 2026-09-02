"""
URL Patterns for Music Catalog & Audio Streaming.
"""
from django.urls import path
from . import views

app_name = 'music'

urlpatterns = [
    # Catalog
    path('songs/', views.SongListView.as_view(), name='song_list'),
    path('songs/<uuid:pk>/', views.SongDetailView.as_view(), name='song_detail'),
    path('stream/<uuid:pk>/', views.SongStreamView.as_view(), name='stream'),
    path('lyrics/<uuid:pk>/', views.SongLyricsAPIView.as_view(), name='lyrics_api'),

    # Creator Studio Operations
    path('upload/', views.SongUploadView.as_view(), name='upload'),
    path('songs/<uuid:pk>/edit/', views.SongEditView.as_view(), name='song_edit'),
    path('songs/<uuid:pk>/delete/', views.SongDeleteView.as_view(), name='song_delete'),

    # Social Reactions
    path('songs/<uuid:pk>/comment/', views.AddTrackCommentView.as_view(), name='add_comment'),
    path('songs/<uuid:pk>/rate/', views.RateSongView.as_view(), name='rate_song'),
]
