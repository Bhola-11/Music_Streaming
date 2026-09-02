"""
Views for Artist Directory, Public Profiles, Creator Studio & Royalty Analytics.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView, CreateView, UpdateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect
from django.db.models import Sum

from .models import Artist, ArtistVerificationRequest, PayoutAccount, RoyaltyStatement, ArtistFollower, VerificationStatus
from .forms import ArtistProfileForm, ArtistVerificationRequestForm, PayoutAccountForm
from music.models import Song
from albums.models import Album
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


class ArtistListView(ListView):
    """
    Public directory of verified creators, producers, and spotlight artists.
    """
    model = Artist
    template_name = 'artists/artist_list.html'
    context_object_name = 'artists'
    paginate_by = 24

    def get_queryset(self):
        qs = Artist.objects.all()
        genre = self.request.GET.get('genre')
        search = self.request.GET.get('q')

        if genre:
            qs = qs.filter(genres__icontains=genre)
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(stage_name__icontains=search)

        return qs.order_by('-monthly_listeners', '-total_streams')


class ArtistDetailView(DetailView):
    """
    Public artist showcase with top tracks, albums, bio, band members, and social links.
    """
    model = Artist
    template_name = 'artists/artist_detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    context_object_name = 'artist'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        artist = self.object
        context['top_tracks'] = (
            Song.objects.filter(artist=artist, is_published=True)
            .order_by('-play_count')[:10]
        )
        context['albums'] = (
            Album.objects.filter(artist=artist, is_published=True)
            .order_by('-release_date')[:12]
        )
        context['members'] = artist.members.filter(is_active=True)
        context['is_following'] = (
            self.request.user.is_authenticated and
            ArtistFollower.objects.filter(user=self.request.user, artist=artist).exists()
        )
        return context


class ArtistStudioDashboardView(LoginRequiredMixin, TemplateView):
    """
    Creator Studio dashboard for managing tracks, viewing real-time stream counts,
    and monitoring payouts.
    """
    template_name = 'artists/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        artist = getattr(user, 'artist_profile', None)

        if not artist:
            context['has_artist_profile'] = False
            return context

        context['has_artist_profile'] = True
        context['artist'] = artist
        context['songs'] = Song.objects.filter(artist=artist).order_by('-created_at')[:10]
        context['albums'] = Album.objects.filter(artist=artist).order_by('-created_at')[:6]
        context['total_plays'] = Song.objects.filter(artist=artist).aggregate(total=Sum('play_count'))['total'] or 0
        context['statements'] = RoyaltyStatement.objects.filter(artist=artist).order_by('-period_start')[:5]
        return context


class ArtistCreateOrEditProfileView(LoginRequiredMixin, View):
    """
    Allows a user to create or update their Artist persona.
    """
    template_name = 'artists/profile_form.html'

    def get(self, request):
        artist = getattr(request.user, 'artist_profile', None)
        form = ArtistProfileForm(instance=artist)
        return render(request, self.template_name, {'form': form, 'artist': artist})

    def post(self, request):
        artist = getattr(request.user, 'artist_profile', None)
        form = ArtistProfileForm(request.POST, request.FILES, instance=artist)

        if form.is_valid():
            artist_obj = form.save(commit=False)
            artist_obj.user = request.user
            artist_obj.save()

            # Upgrade user role to artist
            if request.user.role != 'artist':
                request.user.role = 'artist'
                request.user.save(update_fields=['role'])

            AuditService.log_action(
                action_type='artist.profile_updated',
                category=ActionCategory.ARTIST_ACTION,
                user=request.user,
                description=f"Artist profile '{artist_obj.name}' updated."
            )

            messages.success(request, f"Artist profile for '{artist_obj.name}' saved!")
            return redirect('artists:dashboard')

        return render(request, self.template_name, {'form': form, 'artist': artist})


class ArtistVerificationRequestView(LoginRequiredMixin, CreateView):
    """
    Submit blue verification badge application.
    """
    model = ArtistVerificationRequest
    form_class = ArtistVerificationRequestForm
    template_name = 'artists/verification_request.html'
    success_url = reverse_lazy('artists:dashboard')

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'artist_profile'):
            messages.error(request, "Create an Artist profile first.")
            return redirect('artists:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        req = form.save(commit=False)
        req.artist = self.request.user.artist_profile
        req.status = VerificationStatus.PENDING
        req.save()

        # Update artist status
        self.request.user.artist_profile.verification_status = VerificationStatus.PENDING
        self.request.user.artist_profile.save(update_fields=['verification_status'])

        AuditService.log_action(
            action_type='artist.verification_submitted',
            category=ActionCategory.ARTIST_ACTION,
            user=self.request.user,
            description=f"Verification request filed for {req.artist.name}"
        )
        messages.success(self.request, "Verification request submitted! Our moderation team will review your credentials.")
        return redirect(self.success_url)


class ArtistRoyaltiesView(LoginRequiredMixin, TemplateView):
    """
    Royalty analytics, payout accounts, and payment history.
    """
    template_name = 'artists/royalties.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        artist = getattr(self.request.user, 'artist_profile', None)
        if not artist:
            return context

        context['artist'] = artist
        context['statements'] = RoyaltyStatement.objects.filter(artist=artist).order_by('-period_start')
        context['payout_account'] = getattr(artist, 'payout_account', None)
        context['payout_form'] = PayoutAccountForm(instance=getattr(artist, 'payout_account', None))
        return context

    def post(self, request):
        artist = request.user.artist_profile
        payout_acc = getattr(artist, 'payout_account', None)
        form = PayoutAccountForm(request.POST, instance=payout_acc)
        if form.is_valid():
            acc = form.save(commit=False)
            acc.artist = artist
            acc.save()
            messages.success(request, "Payout account preferences updated!")
            return redirect('artists:royalties')

        context = self.get_context_data()
        context['payout_form'] = form
        return render(request, self.template_name, context)


class ToggleFollowArtistView(LoginRequiredMixin, View):
    """
    Follow or unfollow an artist.
    """
    def post(self, request, slug):
        artist = get_object_or_404(Artist, slug=slug)
        existing = ArtistFollower.objects.filter(user=request.user, artist=artist).first()

        if existing:
            existing.delete()
            artist.follower_count = max(0, artist.follower_count - 1)
            artist.save(update_fields=['follower_count'])
            is_now_following = False
        else:
            ArtistFollower.objects.create(user=request.user, artist=artist)
            artist.follower_count += 1
            artist.save(update_fields=['follower_count'])
            is_now_following = True

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'is_following': is_now_following,
                'follower_count': artist.follower_count
            })

        if is_now_following:
            messages.success(request, f"You are now following {artist.name}.")
        else:
            messages.info(request, f"Unfollowed {artist.name}.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('artists:detail', args=[slug])))
