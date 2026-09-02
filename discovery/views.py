"""
Discovery & Universal Search Views: Discovery Hub, Global Multi-Entity Search,
Trending Charts, and Curated Releases.
"""
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, View
from django.db.models import Q

from .models import FeaturedBanner, MusicChart, ChartEntry, SearchQueryLog, TrendingMetric
from music.models import Song, Genre
from artists.models import Artist
from albums.models import Album
from playlists.models import Playlist, PlaylistPrivacy


class DiscoveryHubView(TemplateView):
    """
    Main discovery portal with animated hero banners, trending songs, charts, and new releases.
    """
    template_name = 'discovery/hub.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hero_banners'] = FeaturedBanner.objects.filter(is_active=True)[:4]
        context['trending_songs'] = Song.objects.filter(is_published=True).select_related('artist', 'genre').order_by('-play_count')[:10]
        context['new_releases'] = Song.objects.filter(is_published=True).select_related('artist').order_by('-created_at')[:8]
        context['top_artists'] = Artist.objects.all().order_by('-monthly_listeners')[:8]
        context['featured_playlists'] = Playlist.objects.filter(privacy=PlaylistPrivacy.PUBLIC, is_featured_curated=True)[:6]
        context['charts'] = MusicChart.objects.filter(is_published=True)[:4]
        context['genres'] = Genre.objects.all()[:12]
        return context


class HomeLandingView(DiscoveryHubView):
    template_name = 'home.html'



class GlobalSearchView(View):
    """
    Universal search engine querying Songs, Artists, Albums, and Playlists concurrently.
    """
    template_name = 'discovery/search.html'

    def get(self, request):
        query = request.GET.get('q', '').strip()
        context = {'query': query}

        if query:
            songs = Song.objects.filter(
                Q(title__icontains=query) | Q(artist__name__icontains=query),
                is_published=True
            ).select_related('artist', 'genre')[:15]

            artists = Artist.objects.filter(
                Q(name__icontains=query) | Q(stage_name__icontains=query)
            )[:8]

            albums = Album.objects.filter(
                Q(title__icontains=query) | Q(artist__name__icontains=query),
                is_published=True
            ).select_related('artist')[:8]

            playlists = Playlist.objects.filter(
                Q(title__icontains=query) | Q(description__icontains=query),
                privacy=PlaylistPrivacy.PUBLIC
            ).select_related('owner')[:8]

            total_hits = len(songs) + len(artists) + len(albums) + len(playlists)

            # Log search analytics
            SearchQueryLog.objects.create(
                query_text=query,
                user=request.user if request.user.is_authenticated else None,
                results_count=total_hits
            )

            context.update({
                'songs': songs,
                'artists': artists,
                'albums': albums,
                'playlists': playlists,
                'total_hits': total_hits,
            })

        return render(request, self.template_name, context)


class TrendingChartsView(ListView):
    """
    Overview of all official MusicVerse charts.
    """
    model = MusicChart
    template_name = 'discovery/charts.html'
    context_object_name = 'charts'

    def get_queryset(self):
        return MusicChart.objects.filter(is_published=True)


class ChartDetailView(DetailView):
    """
    Individual chart track breakdown with rank delta, peak position, and play triggers.
    """
    model = MusicChart
    template_name = 'discovery/chart_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    context_object_name = 'chart'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entries'] = (
            self.object.entries.select_related('song', 'song__artist', 'song__genre')
            .order_by('rank')
        )
        return context
