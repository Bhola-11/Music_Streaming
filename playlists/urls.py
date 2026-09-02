from django.urls import path
from . import views

app_name = 'playlists'

urlpatterns = [
    path('', views.PlaylistListView.as_view(), name='list'),
    path('<slug:slug>/', views.PlaylistDetailView.as_view(), name='detail'),
]
