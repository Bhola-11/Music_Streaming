"""
Master URL Configuration for MusicVerse Platform.
Routes requests cleanly across all 14 decoupled MVT applications.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Core Admin
    path('admin/', admin.site.urls),

    # Accounts & Authentication
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Security & Audit Logs
    path('audit/', include('audit.urls', namespace='audit')),

    # Artists & Creator Studio
    path('artists/', include('artists.urls', namespace='artists')),

    # Music Catalog & Range Streaming
    path('music/', include('music.urls', namespace='music')),

    # Albums & Discography
    path('albums/', include('albums.urls', namespace='albums')),

    # Playlists & Curations
    path('playlists/', include('playlists.urls', namespace='playlists')),

    # Audio Player & Queue
    path('player/', include('player.urls', namespace='player')),

    # Discovery & Charts
    path('discovery/', include('discovery.urls', namespace='discovery')),

    # Personalized Recommendations
    path('recommendations/', include('recommendations.urls', namespace='recommendations')),

    # Subscriptions & Plans
    path('subscriptions/', include('subscriptions.urls', namespace='subscriptions')),

    # Payments & Invoices
    path('payments/', include('payments.urls', namespace='payments')),

    # Notifications & Alerts
    path('notifications/', include('notifications.urls', namespace='notifications')),

    # Analytics Dashboards
    path('analytics/', include('analytics.urls', namespace='analytics')),

    # Content Moderation & Takedowns
    path('moderation/', include('moderation.urls', namespace='moderation')),

    # Default Landing / Home Page
    path('', include('discovery.home_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
