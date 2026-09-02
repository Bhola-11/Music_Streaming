"""
Views for Song Catalog, Streaming Pipeline, Audio Uploads, Lyrics, and Social Reactions.
"""
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse, JsonResponse, Http404
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.db.models import F

from .models import Song, Genre, Mood, Lyrics, TrackComment, TrackRating, SongContributor
from .forms import SongUploadForm, SongEditForm, LyricsForm, TrackCommentForm
from .audio_processor import AudioMetadataExtractor, WaveformPeakGenerator
from .range_streamer import get_range_response
from artists.models import Artist
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


class SongListView(ListView):
    """
    Explore tracks by genre, mood, newest releases, or popular streams.
    """
    model = Song
    template_name = 'music/song_list.html'
    context_object_name = 'songs'
    paginate_by = 28

    def get_queryset(self):
        qs = Song.objects.filter(is_published=True).select_related('artist', 'album', 'genre')
        genre_slug = self.request.GET.get('genre')
        mood_slug = self.request.GET.get('mood')
        sort = self.request.GET.get('sort', '-created_at')

        if genre_slug:
            qs = qs.filter(genre__slug=genre_slug)
        if mood_slug:
            qs = qs.filter(moods__slug=mood_slug)

        if sort == 'popular':
            qs = qs.order_by('-play_count')
        elif sort == 'likes':
            qs = qs.order_by('-like_count')
        else:
            qs = qs.order_by('-created_at')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['genres'] = Genre.objects.all()
        context['moods'] = Mood.objects.all()
        context['current_genre'] = self.request.GET.get('genre', '')
        context['current_mood'] = self.request.GET.get('mood', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        return context


class SongDetailView(DetailView):
    """
    Song master details with lyrics, waveform peaks, contributors, and comments.
    """
    model = Song
    template_name = 'music/song_detail.html'
    context_object_name = 'song'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        song = self.object
        context['lyrics'] = getattr(song, 'lyrics', None)
        context['contributors'] = song.contributors.all()
        context['comments'] = song.comments.select_related('user')[:20]
        context['comment_form'] = TrackCommentForm()
        context['related_tracks'] = (
            Song.objects.filter(genre=song.genre, is_published=True)
            .exclude(id=song.id)
            .select_related('artist')[:6]
        )
        context['user_rating'] = (
            TrackRating.objects.filter(user=self.request.user, song=song).first()
            if self.request.user.is_authenticated else None
        )
        return context


class SongStreamView(View):
    """
    High-performance audio streaming endpoint utilizing HTTP 206 Partial Content.
    """
    def get(self, request, pk):
        song = get_object_or_404(Song, pk=pk, is_published=True)

        if not song.audio_file:
            raise Http404("Master audio file missing.")

        # Premium tier validation
        if song.is_premium_only:
            if not request.user.is_authenticated or not getattr(request.user, 'is_premium', False):
                return HttpResponse("Hi-Fi Pro Subscription Required to stream this track.", status=403)

        # Increment play count on stream start
        Song.objects.filter(id=song.id).update(play_count=F('play_count') + 1)
        Artist.objects.filter(id=song.artist_id).update(total_streams=F('total_streams') + 1)

        file_path = song.audio_file.path
        return get_range_response(request, file_path, content_type='audio/mpeg')


class SongUploadView(LoginRequiredMixin, CreateView):
    """
    Artist portal view for uploading tracks with auto metadata extraction & waveform generation.
    """
    model = Song
    form_class = SongUploadForm
    template_name = 'music/song_upload.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'artist_profile'):
            messages.error(request, "You must create an Artist Profile before publishing songs.")
            return redirect('artists:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        song = form.save(commit=False)
        artist = self.request.user.artist_profile
        song.artist = artist

        audio_file = self.request.FILES.get('audio_file')
        if audio_file:
            # 1. Extract ID3 metadata if user omitted title or bpm
            metadata = AudioMetadataExtractor.extract_metadata(audio_file)
            if not song.title and metadata.get('title'):
                song.title = metadata['title']
            
            song.duration_seconds = metadata.get('duration_seconds', 180)
            song.bitrate_kbps = metadata.get('bitrate_kbps', 320)
            song.sample_rate_hz = metadata.get('sample_rate_hz', 44100)

            # 2. Extract waveform peaks
            waveform = WaveformPeakGenerator.generate_waveform(audio_file, points_count=120)
            song.waveform_data = waveform

        song.save()
        form.save_m2m()

        AuditService.log_action(
            action_type='song.uploaded',
            category=ActionCategory.MUSIC_CATALOG,
            severity=ActionSeverity.INFO,
            user=self.request.user,
            target_model='Song',
            target_object_id=str(song.id),
            target_repr=song.title,
            description=f"Artist '{artist.name}' uploaded song '{song.title}'"
        )

        messages.success(self.request, f"'{song.title}' uploaded and processed successfully!")
        return redirect('music:song_detail', pk=song.id)


class SongEditView(LoginRequiredMixin, UpdateView):
    model = Song
    form_class = SongEditForm
    template_name = 'music/song_edit.html'

    def get_queryset(self):
        return Song.objects.filter(artist__user=self.request.user)

    def get_success_url(self):
        return reverse('music:song_detail', kwargs={'pk': self.object.id})


class SongDeleteView(LoginRequiredMixin, DeleteView):
    model = Song
    template_name = 'music/song_confirm_delete.html'
    success_url = reverse_lazy('artists:dashboard')

    def get_queryset(self):
        return Song.objects.filter(artist__user=self.request.user)


class SongLyricsAPIView(View):
    """
    JSON API returning synchronized or plain lyrics for the player karaoke widget.
    """
    def get(self, request, pk):
        song = get_object_or_404(Song, pk=pk)
        lyrics = getattr(song, 'lyrics', None)
        if not lyrics:
            return JsonResponse({'has_lyrics': False, 'plain': '', 'synced': []})

        return JsonResponse({
            'has_lyrics': True,
            'is_synced': lyrics.is_synced,
            'plain': lyrics.plain_lyrics,
            'synced': lyrics.synced_lyrics_json,
            'writer': lyrics.writer_credit,
        })


class AddTrackCommentView(LoginRequiredMixin, View):
    """
    Submits a comment on a song.
    """
    def post(self, request, pk):
        song = get_object_or_404(Song, pk=pk, is_published=True)
        form = TrackCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.song = song
            comment.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'username': request.user.username,
                    'text': comment.comment_text,
                    'avatar': request.user.avatar_url,
                    'created_at': 'Just now'
                })

            messages.success(request, "Comment posted!")
        return redirect('music:song_detail', pk=song.id)


class RateSongView(LoginRequiredMixin, View):
    """
    Submits 1-5 star rating for a track.
    """
    def post(self, request, pk):
        song = get_object_or_404(Song, pk=pk, is_published=True)
        stars = int(request.POST.get('stars', 5))
        stars = max(1, min(5, stars))

        rating_obj, created = TrackRating.objects.update_or_create(
            user=request.user,
            song=song,
            defaults={'stars': stars}
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'stars': stars})

        messages.success(request, f"You rated '{song.title}' {stars} stars.")
        return redirect('music:song_detail', pk=song.id)
