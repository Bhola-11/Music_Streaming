"""
Views and API Endpoints for Algorithmic Recommendations & 'Made For You' Feed.
"""
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse

from .models import DailyMix, DailyMixTrack
from .services import RecommendationEngine
from music.models import Song


class MadeForYouFeedView(LoginRequiredMixin, TemplateView):
    """
    Algorithmic personal feed: Daily Mixes, Recommended Tracks, and Underground Discoveries.
    """
    template_name = 'recommendations/feed.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Ensure user has daily mixes generated
        mixes = DailyMix.objects.filter(user=user)
        if not mixes.exists():
            mixes = RecommendationEngine.generate_daily_mixes_for_user(user)

        context['daily_mixes'] = mixes
        context['recommended_tracks'] = Song.objects.filter(is_published=True).order_by('?')[:12]
        return context


class DailyMixDetailView(LoginRequiredMixin, DetailView):
    """
    Shows full track sequence of a personalized Daily Mix.
    """
    model = DailyMix
    template_name = 'recommendations/daily_mix_detail.html'
    context_object_name = 'mix'

    def get_queryset(self):
        return DailyMix.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tracks'] = self.object.tracks.select_related('song', 'song__artist', 'song__genre').order_by('position')
        return context


class SimilarTracksAPIView(View):
    """
    JSON API returning tracks similar to a target song.
    """
    def get(self, request, pk):
        song = get_object_or_404(Song, pk=pk)
        similars = RecommendationEngine.get_similar_songs(song, limit=8)

        tracks = []
        for s in similars:
            tracks.append({
                'id': str(s.id),
                'title': s.title,
                'artist': s.artist.name,
                'cover_art': s.cover_art_url,
                'stream_url': reverse('music:stream', args=[s.id]),
                'duration': s.formatted_duration,
            })
        return JsonResponse({'success': True, 'similar_tracks': tracks})
