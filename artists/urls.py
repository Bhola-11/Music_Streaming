"""
URL routing for Artists & Creator Studio.
"""
from django.urls import path
from . import views

app_name = 'artists'

urlpatterns = [
    # Directory
    path('', views.ArtistListView.as_view(), name='list'),

    # Creator Studio
    path('studio/dashboard/', views.ArtistStudioDashboardView.as_view(), name='dashboard'),
    path('studio/profile/edit/', views.ArtistCreateOrEditProfileView.as_view(), name='edit_profile'),
    path('studio/verification/', views.ArtistVerificationRequestView.as_view(), name='verification_request'),
    path('studio/royalties/', views.ArtistRoyaltiesView.as_view(), name='royalties'),

    # Public Artist Profile & Social Graph
    path('<slug:slug>/', views.ArtistDetailView.as_view(), name='detail'),
    path('<slug:slug>/toggle-follow/', views.ToggleFollowArtistView.as_view(), name='toggle_follow'),
]
