"""
URL Routing for Albums & Discography.
"""
from django.urls import path
from . import views

app_name = 'albums'

urlpatterns = [
    path('', views.AlbumListView.as_view(), name='list'),
    path('create/', views.AlbumCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.AlbumDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.AlbumEditView.as_view(), name='edit'),
    path('<slug:slug>/review/', views.AddAlbumReviewView.as_view(), name='add_review'),
]
