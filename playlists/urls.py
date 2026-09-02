"""
URL Routing for Playlists & Collaborative Curation.
"""
from django.urls import path
from . import views

app_name = 'playlists'

urlpatterns = [
    path('', views.PlaylistListView.as_view(), name='list'),
    path('me/', views.UserPlaylistsView.as_view(), name='user_playlists'),
    path('create/', views.PlaylistCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.PlaylistDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.PlaylistEditView.as_view(), name='edit'),
    path('<slug:slug>/delete/', views.PlaylistDeleteView.as_view(), name='delete'),
    path('<slug:slug>/follow/', views.ToggleFollowPlaylistView.as_view(), name='toggle_follow'),
    path('<slug:slug>/collaborators/', views.ManageCollaboratorsView.as_view(), name='manage_collaborators'),

    # AJAX APIs
    path('<uuid:pk>/add-track/', views.AddTrackToPlaylistAPIView.as_view(), name='api_add_track'),
    path('<uuid:playlist_pk>/remove-track/<uuid:song_pk>/', views.RemoveTrackFromPlaylistAPIView.as_view(), name='api_remove_track'),
    path('<uuid:pk>/reorder/', views.ReorderPlaylistTracksAPIView.as_view(), name='api_reorder_tracks'),
]
