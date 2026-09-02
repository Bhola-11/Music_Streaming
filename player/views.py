"""
Audio Player Views & JSON APIs: Queue Management, Playback History,
Favorite Tracks Library, and Dynamic Genre/Mood Radio Generation.
"""
import json
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import F

from .models import PlaybackQueue, QueueItem, ListeningHistory, FavoriteTrack, PlaybackSession, RadioStation
from music.models import Song, Genre


class FavoritesListView(LoginRequiredMixin, ListView):
    """
    Renders user's 'Liked Songs' personal library.
    """
    model = FavoriteTrack
    template_name = 'player/favorites.html'
    context_object_name = 'favorites'
    paginate_by = 50

    def get_queryset(self):
        return (
            FavoriteTrack.objects.filter(user=self.request.user)
            .select_related('song', 'song__artist', 'song__genre')
            .order_by('-created_at')
        )


class ListeningHistoryListView(LoginRequiredMixin, ListView):
    """
    Renders user's complete audio playback logs and listening stats.
    """
    model = ListeningHistory
    template_name = 'player/history.html'
    context_object_name = 'history'
    paginate_by = 50

    def get_queryset(self):
        return (
            ListeningHistory.objects.filter(user=self.request.user)
            .select_related('song', 'song__artist')
            .order_by('-played_at')
        )


class ToggleFavoriteTrackAPIView(LoginRequiredMixin, View):
    """
    AJAX endpoint to like/unlike a track.
    """
    def post(self, request, pk):
        song = get_object_or_404(Song, pk=pk)
        existing = FavoriteTrack.objects.filter(user=request.user, song=song).first()

        if existing:
            existing.delete()
            Song.objects.filter(id=song.id).update(like_count=F('like_count') - 1)
            is_favorite = False
        else:
            FavoriteTrack.objects.create(user=request.user, song=song)
            Song.objects.filter(id=song.id).update(like_count=F('like_count') + 1)
            is_favorite = True

        return JsonResponse({
            'success': True,
            'is_favorite': is_favorite,
            'song_id': str(song.id),
            'like_count': Song.objects.get(id=song.id).like_count
        })


class RecordPlaybackHistoryAPIView(View):
    """
    Called by player_engine.js on track completion or seek to record stream metrics.
    """
    def post(self, request, pk):
        song = get_object_or_404(Song, pk=pk)
        data = {}
        if request.body:
            try:
                data = json.loads(request.body)
            except Exception:
                pass

        seconds_played = int(data.get('seconds_played', 0))
        completion_pct = float(data.get('completion_pct', 0.0))
        was_skipped = bool(data.get('was_skipped', False))
        device_info = data.get('device_info', request.META.get('HTTP_USER_AGENT', 'Web')[:180])
        ip = request.META.get('REMOTE_ADDR')

        if request.user.is_authenticated:
            ListeningHistory.objects.create(
                user=request.user,
                song=song,
                seconds_played=seconds_played,
                completion_percentage=completion_pct,
                was_skipped=was_skipped,
                device_info=device_info,
                ip_address=ip
            )

        return JsonResponse({'success': True, 'recorded': True})


class GetActiveQueueAPIView(LoginRequiredMixin, View):
    """
    Returns full playback queue in sequence for the player frontend.
    """
    def get(self, request):
        queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)
        items = queue.items.select_related('song', 'song__artist', 'song__genre').order_by('position')

        tracks = []
        for item in items:
            s = item.song
            tracks.append({
                'queue_item_id': str(item.id),
                'id': str(s.id),
                'title': s.title,
                'artist': s.artist.name,
                'cover_art': s.cover_art_url,
                'stream_url': reverse('music:stream', args=[s.id]),
                'duration': s.duration_seconds,
                'formatted_duration': s.formatted_duration,
                'bitrate': s.bitrate_kbps,
                'waveform': s.waveform_data,
            })

        return JsonResponse({'success': True, 'queue': tracks})


class QueueAddAPIView(LoginRequiredMixin, View):
    """
    Appends track to user's Up Next queue.
    """
    def post(self, request, pk):
        song = get_object_or_404(Song, pk=pk)
        queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)
        max_pos = queue.items.count()

        item = QueueItem.objects.create(
            queue=queue,
            song=song,
            position=max_pos + 1
        )
        return JsonResponse({
            'success': True,
            'message': f"Added '{song.title}' to queue",
            'queue_length': max_pos + 1
        })


class QueueRemoveAPIView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(QueueItem, id=item_id, queue__user=request.user)
        item.delete()
        return JsonResponse({'success': True, 'message': 'Removed from queue'})


class QueueClearAPIView(LoginRequiredMixin, View):
    def post(self, request):
        queue = PlaybackQueue.objects.filter(user=request.user).first()
        if queue:
            queue.items.all().delete()
        return JsonResponse({'success': True, 'message': 'Queue cleared'})


class StartRadioFromSongAPIView(View):
    """
    Generates an algorithmic radio session seeded by genre/mood of chosen track.
    """
    def get(self, request, pk):
        seed_song = get_object_or_404(Song, pk=pk)
        # Find 15 similar songs in same genre/mood
        similar_tracks = (
            Song.objects.filter(is_published=True)
            .filter(genre=seed_song.genre)
            .exclude(id=seed_song.id)
            .order_by('?')[:15]
        )

        radio_playlist = [seed_song] + list(similar_tracks)
        tracks = []
        for s in radio_playlist:
            tracks.append({
                'id': str(s.id),
                'title': s.title,
                'artist': s.artist.name,
                'cover_art': s.cover_art_url,
                'stream_url': reverse('music:stream', args=[s.id]),
                'duration': s.duration_seconds,
                'formatted_duration': s.formatted_duration,
                'waveform': s.waveform_data,
            })

        return JsonResponse({'success': True, 'seed_title': seed_song.title, 'radio_tracks': tracks})
