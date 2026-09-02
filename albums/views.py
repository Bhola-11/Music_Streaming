"""
Views for Albums, Track Listings, Creator Album Builder, and Community Reviews.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse

from .models import Album, AlbumTrack, DiscEdition, AlbumReview
from .forms import AlbumForm, AlbumReviewForm
from music.models import Song
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


class AlbumListView(ListView):
    """
    Lists studio albums, EPs, and discographies.
    """
    model = Album
    template_name = 'albums/album_list.html'
    context_object_name = 'albums'
    paginate_by = 24

    def get_queryset(self):
        qs = Album.objects.filter(is_published=True).select_related('artist', 'record_label')
        album_type = self.request.GET.get('type')
        if album_type:
            qs = qs.filter(album_type=album_type)
        return qs.order_by('-release_date', '-created_at')


class AlbumDetailView(DetailView):
    """
    Full album showcase with sequenced track list, total runtime, reviews, and editions.
    """
    model = Album
    template_name = 'albums/album_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    context_object_name = 'album'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.object
        context['tracks'] = (
            AlbumTrack.objects.filter(album=album)
            .select_related('song', 'song__artist')
            .order_by('disc_number', 'track_number')
        )
        context['reviews'] = album.reviews.select_related('user')[:15]
        context['review_form'] = AlbumReviewForm()
        context['editions'] = album.editions.all()
        return context


class AlbumCreateView(LoginRequiredMixin, CreateView):
    """
    Artist portal view for creating albums.
    """
    model = Album
    form_class = AlbumForm
    template_name = 'albums/album_create.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'artist_profile'):
            messages.error(request, "You must create an Artist Profile first.")
            return redirect('artists:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        album = form.save(commit=False)
        album.artist = self.request.user.artist_profile
        album.save()

        AuditService.log_action(
            action_type='album.created',
            category=ActionCategory.MUSIC_CATALOG,
            user=self.request.user,
            target_model='Album',
            target_object_id=str(album.id),
            target_repr=album.title,
            description=f"Artist '{album.artist.name}' created album '{album.title}'"
        )
        messages.success(self.request, f"Album '{album.title}' created! Now add tracks to it.")
        return redirect('albums:detail', slug=album.slug)


class AlbumEditView(LoginRequiredMixin, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = 'albums/album_edit.html'

    def get_queryset(self):
        return Album.objects.filter(artist__user=self.request.user)

    def get_success_url(self):
        return reverse('albums:detail', kwargs={'slug': self.object.slug})


class AddAlbumReviewView(LoginRequiredMixin, View):
    """
    Submits or updates a user critique on an album.
    """
    def post(self, request, slug):
        album = get_object_or_404(Album, slug=slug, is_published=True)
        form = AlbumReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.album = album
            review.save()
            messages.success(request, "Thank you for your album review!")
        else:
            messages.error(request, "Please verify your review inputs.")
        return redirect('albums:detail', slug=album.slug)
