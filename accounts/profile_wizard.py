"""
Multi-step Onboarding & Profile Wizard.
Guides newly registered users through music genre preferences, artist recommendations,
audio quality selection, and creator profile setup.
"""
from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from music.models import Genre
from artists.models import Artist
from .models import UserRole, UserPreferences
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


class OnboardingWizardView(LoginRequiredMixin, View):
    """
    Step 1: Choose Favorite Genres
    Step 2: Follow Recommended Artists
    Step 3: Choose Audio Fidelity & Theme
    """
    template_name = 'accounts/onboarding_wizard.html'

    def get_step(self):
        return int(self.request.GET.get('step', 1))

    def get(self, request):
        step = self.get_step()
        context = {'current_step': step}

        if step == 1:
            context['genres'] = Genre.objects.all()[:18]
        elif step == 2:
            context['artists'] = Artist.objects.all()[:12]
        elif step == 3:
            context['preferences'] = request.user.preferences
        else:
            return redirect('home')

        return render(request, self.template_name, context)

    def post(self, request):
        step = self.get_step()

        if step == 1:
            selected_genre_ids = request.POST.getlist('genres')
            # Save temporary preferences in session
            request.session['onboarding_genres'] = selected_genre_ids
            return redirect(f"{request.path}?step=2")

        elif step == 2:
            selected_artist_ids = request.POST.getlist('artists')
            request.session['onboarding_artists'] = selected_artist_ids
            return redirect(f"{request.path}?step=3")

        elif step == 3:
            audio_quality = request.POST.get('audio_quality', 'standard')
            theme = request.POST.get('theme', 'dark-cosmic')
            visualizer = request.POST.get('visualizer_mode', '3d-particle-mesh')

            prefs = request.user.preferences
            prefs.audio_quality = audio_quality
            prefs.theme = theme
            prefs.visualizer_mode = visualizer
            prefs.save()

            # Mark user as onboarding completed
            request.user.is_verified = True
            request.user.save(update_fields=['is_verified'])

            AuditService.log_action(
                action_type='user.onboarding_completed',
                category=ActionCategory.USER_MANAGEMENT,
                severity=ActionSeverity.INFO,
                user=request.user,
                description=f"User {request.user.username} completed onboarding wizard"
            )

            messages.success(request, "Your sonic profile is configured! Enjoy streaming.")
            return redirect('home')

        return redirect('home')
