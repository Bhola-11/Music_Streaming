"""
Discovery, Trending, Search and Landing Page Views.
"""
from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from music.models import Song, Genre
from artists.models import Artist
from albums.models import Album
from playlists.models import Playlist


class HomeLandingView(TemplateView):
    """
    Main MusicVerse Landing / Hub page showcasing 3D visualizers,
    trending releases, top artists, and recommended playlists.
    """
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_songs'] = Song.objects.filter(is_published=True).select_related('artist', 'album')[:10]
        context['trending_artists'] = Artist.objects.all()[:8]
        context['new_albums'] = Album.objects.filter(is_published=True).select_related('artist')[:8]
        context['featured_playlists'] = Playlist.objects.filter(is_public=True).select_related('creator')[:6]
        context['genres'] = Genre.objects.all()[:12]
        return context


class DiscoveryHubView(TemplateView):
    template_name = 'discovery/hub.html'


class SearchGlobalView(TemplateView):
    template_name = 'discovery/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        if query:
            context['songs'] = Song.objects.filter(title__icontains=query, is_published=True)[:15]
            context['artists'] = Artist.objects.filter(name__icontains=query)[:8]
            context['albums'] = Album.objects.filter(title__icontains=query, is_published=True)[:8]
            context['playlists'] = Playlist.objects.filter(title__icontains=query, is_public=True)[:8]
        else:
            context['songs'] = []
            context['artists'] = []
            context['albums'] = []
            context['playlists'] = []
        return context
