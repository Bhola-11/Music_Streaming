"""
Views for Playlist Discovery, Creation, Collaborative Editing,
Sequenced Track Reordering, and Social Bookmarking.
"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Max, Q

from .models import Playlist, PlaylistTrack, PlaylistCollaborator, PlaylistFollower, PlaylistPrivacy, CollaboratorRole
from .forms import PlaylistForm, AddCollaboratorForm
from music.models import Song
from notifications.services import NotificationService
from notifications.models import NotificationType
from audit.services import AuditService
from audit.models import ActionCategory


class PlaylistListView(ListView):
    """
    Public and featured editorial playlists.
    """
    model = Playlist
    template_name = 'playlists/playlist_list.html'
    context_object_name = 'playlists'
    paginate_by = 24

    def get_queryset(self):
        return Playlist.objects.filter(privacy=PlaylistPrivacy.PUBLIC).select_related('owner').order_by('-is_featured_curated', '-follower_count')


class UserPlaylistsView(LoginRequiredMixin, ListView):
    """
    User's library of created and collaborative playlists.
    """
    model = Playlist
    template_name = 'playlists/user_playlists.html'
    context_object_name = 'playlists'

    def get_queryset(self):
        user = self.request.user
        return Playlist.objects.filter(
            Q(owner=user) | Q(collaborators__user=user)
        ).distinct().order_by('-created_at')


class PlaylistDetailView(DetailView):
    """
    Detailed playlist page with sequenced tracks, drag-and-drop handles, and playback controls.
    """
    model = Playlist
    template_name = 'playlists/playlist_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    context_object_name = 'playlist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        playlist = self.object
        user = self.request.user

        context['tracks'] = (
            PlaylistTrack.objects.filter(playlist=playlist)
            .select_related('song', 'song__artist', 'added_by')
            .order_by('position')
        )
        context['collaborators'] = playlist.collaborators.select_related('user')
        context['is_owner'] = user.is_authenticated and playlist.owner == user
        context['is_collaborator'] = (
            user.is_authenticated and
            playlist.collaborators.filter(user=user).exists()
        )
        context['can_edit'] = (
            context['is_owner'] or
            (playlist.is_collaborative and context['is_collaborator'])
        )
        context['is_following'] = (
            user.is_authenticated and
            PlaylistFollower.objects.filter(user=user, playlist=playlist).exists()
        )
        context['collab_form'] = AddCollaboratorForm()
        return context


class PlaylistCreateView(LoginRequiredMixin, CreateView):
    model = Playlist
    form_class = PlaylistForm
    template_name = 'playlists/playlist_form.html'

    def form_valid(self, form):
        playlist = form.save(commit=False)
        playlist.owner = self.request.user
        playlist.save()

        AuditService.log_action(
            action_type='playlist.created',
            category=ActionCategory.USER_MANAGEMENT,
            user=self.request.user,
            target_model='Playlist',
            target_object_id=str(playlist.id),
            target_repr=playlist.title
        )

        messages.success(self.request, f"Playlist '{playlist.title}' created!")
        return redirect('playlists:detail', slug=playlist.slug)


class PlaylistEditView(LoginRequiredMixin, UpdateView):
    model = Playlist
    form_class = PlaylistForm
    template_name = 'playlists/playlist_form.html'

    def get_queryset(self):
        return Playlist.objects.filter(owner=self.request.user)

    def get_success_url(self):
        return reverse('playlists:detail', kwargs={'slug': self.object.slug})


class PlaylistDeleteView(LoginRequiredMixin, DeleteView):
    model = Playlist
    template_name = 'playlists/playlist_confirm_delete.html'
    success_url = reverse_lazy('playlists:user_playlists')

    def get_queryset(self):
        return Playlist.objects.filter(owner=self.request.user)


class AddTrackToPlaylistAPIView(LoginRequiredMixin, View):
    """
    Adds a song to a playlist with automatic end-of-list sequencing.
    """
    def post(self, request, pk):
        playlist = get_object_or_404(Playlist, pk=pk)
        user = request.user

        # Permission check
        is_collab = playlist.collaborators.filter(user=user, role__in=[CollaboratorRole.EDITOR, CollaboratorRole.ADMIN]).exists()
        if playlist.owner != user and not (playlist.is_collaborative and is_collab):
            return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

        song_id = request.POST.get('song_id')
        song = get_object_or_404(Song, pk=song_id)

        # Check existing
        if PlaylistTrack.objects.filter(playlist=playlist, song=song).exists():
            return JsonResponse({'success': False, 'error': 'Song is already in this playlist.'}, status=400)

        # Compute next position
        max_pos = PlaylistTrack.objects.filter(playlist=playlist).aggregate(m=Max('position'))['m'] or 0
        track = PlaylistTrack.objects.create(
            playlist=playlist,
            song=song,
            added_by=user,
            position=max_pos + 1
        )

        # Notify owner if added by collaborator
        if playlist.owner != user:
            NotificationService.send_notification(
                recipient=playlist.owner,
                notification_type=NotificationType.PLAYLIST_ADD,
                title=f"New track added to '{playlist.title}'",
                message=f"{user.username} added '{song.title}' to your playlist.",
                action_url=reverse('playlists:detail', args=[playlist.slug])
            )

        return JsonResponse({
            'success': True,
            'message': f"Added '{song.title}' to {playlist.title}",
            'track_id': str(track.id),
            'position': track.position
        })


class RemoveTrackFromPlaylistAPIView(LoginRequiredMixin, View):
    """
    Removes a track from a playlist.
    """
    def post(self, request, playlist_pk, song_pk):
        playlist = get_object_or_404(Playlist, pk=playlist_pk)
        user = request.user

        is_collab = playlist.collaborators.filter(user=user, role__in=[CollaboratorRole.EDITOR, CollaboratorRole.ADMIN]).exists()
        if playlist.owner != user and not (playlist.is_collaborative and is_collab):
            return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

        pt = PlaylistTrack.objects.filter(playlist=playlist, song_id=song_pk).first()
        if pt:
            pt.delete()
            # Re-index positions
            tracks = PlaylistTrack.objects.filter(playlist=playlist).order_by('position')
            for index, item in enumerate(tracks, start=1):
                if item.position != index:
                    item.position = index
                    item.save(update_fields=['position'])

            return JsonResponse({'success': True, 'message': 'Track removed from playlist.'})
        return JsonResponse({'success': False, 'error': 'Track not found.'}, status=404)


class ReorderPlaylistTracksAPIView(LoginRequiredMixin, View):
    """
    AJAX endpoint for drag-and-drop track re-indexing.
    Accepts: JSON {"order": ["song-uuid-1", "song-uuid-2", ...]}
    """
    def post(self, request, pk):
        playlist = get_object_or_404(Playlist, pk=pk)
        user = request.user

        is_collab = playlist.collaborators.filter(user=user, role__in=[CollaboratorRole.EDITOR, CollaboratorRole.ADMIN]).exists()
        if playlist.owner != user and not (playlist.is_collaborative and is_collab):
            return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)

        try:
            data = json.loads(request.body)
            order_list = data.get('order', [])
            for index, song_id in enumerate(order_list, start=1):
                PlaylistTrack.objects.filter(playlist=playlist, song_id=song_id).update(position=index)
            return JsonResponse({'success': True, 'message': 'Playlist order saved.'})
        except Exception as exc:
            return JsonResponse({'success': False, 'error': str(exc)}, status=400)


class ToggleFollowPlaylistView(LoginRequiredMixin, View):
    """
    Follow/bookmark a public playlist.
    """
    def post(self, request, slug):
        playlist = get_object_or_404(Playlist, slug=slug)
        user = request.user
        existing = PlaylistFollower.objects.filter(playlist=playlist, user=user).first()

        if existing:
            existing.delete()
            playlist.follower_count = max(0, playlist.follower_count - 1)
            playlist.save(update_fields=['follower_count'])
            is_following = False
        else:
            PlaylistFollower.objects.create(playlist=playlist, user=user)
            playlist.follower_count += 1
            playlist.save(update_fields=['follower_count'])
            is_following = True

            if playlist.owner != user:
                NotificationService.send_notification(
                    recipient=playlist.owner,
                    notification_type=NotificationType.NEW_FOLLOWER,
                    title="New Playlist Follower",
                    message=f"{user.username} is now following your playlist '{playlist.title}'.",
                    action_url=reverse('playlists:detail', args=[playlist.slug])
                )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'is_following': is_following, 'follower_count': playlist.follower_count})

        messages.success(request, f"{'Saved to' if is_following else 'Removed from'} your library.")
        return redirect('playlists:detail', slug=playlist.slug)


class ManageCollaboratorsView(LoginRequiredMixin, View):
    """
    Adds or removes collaborators from a playlist.
    """
    def post(self, request, slug):
        playlist = get_object_or_404(Playlist, slug=slug, owner=request.user)
        form = AddCollaboratorForm(request.POST)
        if form.is_valid():
            collaborator_user = form.cleaned_data['username_or_email']
            role = form.cleaned_data['role']

            if collaborator_user == playlist.owner:
                messages.error(request, "You are already the owner of this playlist.")
            else:
                collab, created = PlaylistCollaborator.objects.update_or_create(
                    playlist=playlist,
                    user=collaborator_user,
                    defaults={'role': role}
                )
                playlist.is_collaborative = True
                playlist.save(update_fields=['is_collaborative'])

                NotificationService.send_notification(
                    recipient=collaborator_user,
                    notification_type=NotificationType.PLAYLIST_ADD,
                    title="Playlist Collaboration Invite",
                    message=f"{request.user.username} invited you as a {collab.get_role_display()} on '{playlist.title}'.",
                    action_url=reverse('playlists:detail', args=[playlist.slug])
                )
                messages.success(request, f"Added {collaborator_user.username} as {collab.get_role_display()}!")
        else:
            messages.error(request, "User could not be found.")
        return redirect('playlists:detail', slug=playlist.slug)
