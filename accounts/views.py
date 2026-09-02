"""
Views for Accounts, Authentication, Profile, Security & Session Management.
"""
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import View, FormView, DetailView, UpdateView, TemplateView, ListView

from .models import User, UserProfile, UserPreferences, TwoFactorAuth, UserSession, UserFollow, UserRole
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
    UserPreferencesForm,
    TwoFactorVerifyForm,
    SecurityQuestionForm,
)
from .services import AuthenticationService, TwoFactorService, SessionManagementService, ProfileService
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


class RegisterView(FormView):
    """
    Handles user onboarding and account creation with audit logging.
    """
    template_name = 'accounts/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            f"Welcome to MusicVerse, {user.username}! Your cosmic audio journey starts now."
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below to register.")
        return super().form_invalid(form)


class LoginView(FormView):
    """
    Authenticates users via email and password with support for 2FA challenges.
    """
    template_name = 'accounts/login.html'
    form_class = UserLoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        remember_me = form.cleaned_data.get('remember_me', False)

        user, error_msg = AuthenticationService.authenticate_user(self.request, email, password)

        if not user:
            messages.error(self.request, error_msg or "Invalid email or password.")
            return self.form_invalid(form)

        # Check if 2FA is enabled
        if hasattr(user, 'two_factor') and user.two_factor.is_enabled:
            # Store temporary auth state in session
            self.request.session['2fa_pre_auth_user_id'] = str(user.id)
            self.request.session['2fa_remember_me'] = remember_me
            return redirect('accounts:two_factor_verify')

        # Standard login
        login(self.request, user)
        if not remember_me:
            self.request.session.set_expiry(0)  # Expires when browser closes
        else:
            self.request.session.set_expiry(1209600)  # 2 weeks

        messages.success(self.request, f"Welcome back, {user.username}!")
        next_url = self.request.GET.get('next')
        return redirect(next_url if next_url else 'home')


class TwoFactorVerifyView(FormView):
    """
    Validates TOTP token or one-time backup code for two-factor enabled accounts.
    """
    template_name = 'accounts/two_factor_verify.html'
    form_class = TwoFactorVerifyForm

    def get_pre_auth_user(self):
        user_id = self.request.session.get('2fa_pre_auth_user_id')
        if not user_id:
            return None
        return User.objects.filter(id=user_id, is_active=True).first()

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        if not self.get_pre_auth_user():
            messages.warning(request, "Session expired or invalid. Please sign in again.")
            return redirect('accounts:login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = self.get_pre_auth_user()
        code = form.cleaned_data['code'].strip()
        two_factor = user.two_factor

        is_valid = TwoFactorService.verify_totp(two_factor.secret_key, code)

        if not is_valid:
            # Check backup code
            is_valid = TwoFactorService.verify_and_consume_backup_code(two_factor, code)

        if is_valid:
            # Mark 2FA timestamp
            two_factor.last_used_at = timezone.now()
            two_factor.save(update_fields=['last_used_at'])

            # Complete login
            login(self.request, user)
            remember_me = self.request.session.pop('2fa_remember_me', False)
            self.request.session.pop('2fa_pre_auth_user_id', None)

            if not remember_me:
                self.request.session.set_expiry(0)

            AuditService.log_action(
                action_type='auth.2fa_success',
                category=ActionCategory.AUTHENTICATION,
                user=user,
                description=f"2FA verified successfully for {user.email}"
            )
            messages.success(self.request, f"Identity verified. Welcome back, {user.username}!")
            return redirect('home')
        else:
            AuditService.log_security_event(
                event_type='2fa_verification_failed',
                user=user,
                source_ip=self.request.META.get('REMOTE_ADDR', '127.0.0.1'),
                details={'code_attempt': code}
            )
            messages.error(self.request, "Invalid authentication code. Please check your authenticator app.")
            return self.form_invalid(form)


class LogoutView(View):
    """
    Logs out the user and clears session state.
    """
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            AuditService.log_action(
                action_type='user.logout',
                category=ActionCategory.AUTHENTICATION,
                user=request.user,
                description=f"User {request.user.email} logged out"
            )
            logout(request)
            messages.info(request, "You have been successfully logged out.")
        return redirect('accounts:login')


class ProfileView(DetailView):
    """
    Public or private profile view with music stats, public playlists, and creator links.
    """
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        context['is_own_profile'] = self.request.user == user
        context['is_following'] = (
            self.request.user.is_authenticated and
            UserFollow.objects.filter(follower=self.request.user, following=user).exists()
        )
        context['followers_count'] = UserFollow.objects.filter(following=user).count()
        context['following_count'] = UserFollow.objects.filter(follower=user).count()

        # Public Playlists
        if hasattr(user, 'created_playlists'):
            if context['is_own_profile']:
                context['playlists'] = user.created_playlists.all()[:12]
            else:
                context['playlists'] = user.created_playlists.filter(is_public=True)[:12]
        else:
            context['playlists'] = []

        return context


class EditProfileView(LoginRequiredMixin, UpdateView):
    """
    Update profile details, bio, avatar, and social links.
    """
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:edit_profile')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        profile = form.save(commit=False)
        user = self.request.user
        user.first_name = form.cleaned_data.get('first_name', '')
        user.last_name = form.cleaned_data.get('last_name', '')
        user.phone = form.cleaned_data.get('phone', '')

        # Update avatar & banner if provided
        if self.request.FILES.get('avatar'):
            user.avatar = self.request.FILES['avatar']
        if self.request.FILES.get('header_banner'):
            profile.header_banner = self.request.FILES['header_banner']

        # Social links mapping
        profile.social_links = {
            'twitter': form.cleaned_data.get('twitter_url', ''),
            'instagram': form.cleaned_data.get('instagram_url', ''),
            'spotify': form.cleaned_data.get('spotify_url', ''),
            'soundcloud': form.cleaned_data.get('soundcloud_url', ''),
        }

        user.save()
        profile.save()

        messages.success(self.request, "Your profile has been updated successfully!")
        return redirect(self.get_success_url())


class PreferencesView(LoginRequiredMixin, UpdateView):
    """
    Manages streaming quality, visualizer mode, theme, and notification preferences.
    """
    model = UserPreferences
    form_class = UserPreferencesForm
    template_name = 'accounts/preferences.html'
    success_url = reverse_lazy('accounts:preferences')

    def get_object(self, queryset=None):
        return self.request.user.preferences

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your audio and visual preferences have been saved!")
        return redirect(self.get_success_url())


class SecuritySettingsView(LoginRequiredMixin, TemplateView):
    """
    Security dashboard: change password, active devices/sessions, and 2FA status.
    """
    template_name = 'accounts/security.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['has_2fa'] = hasattr(user, 'two_factor') and user.two_factor.is_enabled
        context['sessions'] = SessionManagementService.get_user_sessions(user)[:10]
        context['password_form'] = PasswordChangeForm(user=user)
        return context

    def post(self, request, *args, **kwargs):
        password_form = PasswordChangeForm(user=request.user, data=request.POST)
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            AuditService.log_action(
                action_type='user.password_change',
                category=ActionCategory.AUTHENTICATION,
                severity=ActionSeverity.LOW,
                user=user,
                description=f"User {user.email} changed password successfully"
            )
            messages.success(request, "Your password has been changed successfully!")
            return redirect('accounts:security')
        else:
            messages.error(request, "Please correct the password errors below.")
            context = self.get_context_data()
            context['password_form'] = password_form
            return render(request, self.template_name, context)


class TwoFactorSetupView(LoginRequiredMixin, View):
    """
    Generates TOTP secret, backup recovery codes, and handles verification for enabling 2FA.
    """
    template_name = 'accounts/two_factor_setup.html'

    def get(self, request):
        secret_key = TwoFactorService.generate_secret()
        plain_codes, hashed_codes = TwoFactorService.generate_backup_codes(8)
        
        # Save provisional secret in session
        request.session['provisional_2fa_secret'] = secret_key
        request.session['provisional_2fa_backup_hashes'] = hashed_codes

        otp_auth_url = f"otpauth://totp/MusicVerse:{request.user.email}?secret={secret_key}&issuer=MusicVerse"

        return render(request, self.template_name, {
            'secret_key': secret_key,
            'otp_auth_url': otp_auth_url,
            'backup_codes': plain_codes,
            'form': TwoFactorVerifyForm(),
        })

    def post(self, request):
        form = TwoFactorVerifyForm(request.POST)
        secret_key = request.session.get('provisional_2fa_secret')
        backup_hashes = request.session.get('provisional_2fa_backup_hashes')

        if not secret_key:
            messages.error(request, "2FA setup session expired. Please start setup again.")
            return redirect('accounts:two_factor_setup')

        if form.is_valid():
            code = form.cleaned_data['code'].strip()
            if TwoFactorService.verify_totp(secret_key, code):
                two_factor_obj, _ = TwoFactorAuth.objects.get_or_create(user=request.user)
                two_factor_obj.secret_key = secret_key
                two_factor_obj.backup_codes = backup_hashes
                two_factor_obj.is_enabled = True
                two_factor_obj.last_used_at = timezone.now()
                two_factor_obj.save()

                # Clear session keys
                request.session.pop('provisional_2fa_secret', None)
                request.session.pop('provisional_2fa_backup_hashes', None)

                AuditService.log_action(
                    action_type='auth.2fa_enabled',
                    category=ActionCategory.AUTHENTICATION,
                    severity=ActionSeverity.MEDIUM,
                    user=request.user,
                    description=f"2FA enabled for account {request.user.email}"
                )
                messages.success(request, "Two-Factor Authentication is now enabled for your account!")
                return redirect('accounts:security')
            else:
                messages.error(request, "The 6-digit code was invalid. Please ensure the code is correct.")

        return render(request, self.template_name, {
            'secret_key': secret_key,
            'otp_auth_url': f"otpauth://totp/MusicVerse:{request.user.email}?secret={secret_key}&issuer=MusicVerse",
            'form': form,
        })


class TwoFactorDisableView(LoginRequiredMixin, View):
    """
    Disables 2FA on the user account after password re-verification.
    """
    def post(self, request):
        password = request.POST.get('password', '')
        if not request.user.check_password(password):
            messages.error(request, "Incorrect password. Unable to disable Two-Factor Authentication.")
            return redirect('accounts:security')

        if hasattr(request.user, 'two_factor'):
            request.user.two_factor.is_enabled = False
            request.user.two_factor.save(update_fields=['is_enabled'])

            AuditService.log_action(
                action_type='auth.2fa_disabled',
                category=ActionCategory.AUTHENTICATION,
                severity=ActionSeverity.HIGH,
                user=request.user,
                description=f"2FA disabled for account {request.user.email}"
            )
            messages.warning(request, "Two-Factor Authentication has been disabled.")

        return redirect('accounts:security')


class ActiveSessionsView(LoginRequiredMixin, ListView):
    """
    Lists all active browser/mobile sessions for the user.
    """
    model = UserSession
    template_name = 'accounts/sessions.html'
    context_object_name = 'sessions'

    def get_queryset(self):
        return SessionManagementService.get_user_sessions(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_session_key'] = self.request.session.session_key
        return context


class TerminateSessionView(LoginRequiredMixin, View):
    """
    Revokes a specific session.
    """
    def post(self, request, session_key):
        success = SessionManagementService.terminate_session(request.user, session_key)
        if success:
            messages.success(request, "The selected session was successfully terminated.")
        else:
            messages.error(request, "Session could not be found or terminated.")
        return redirect('accounts:sessions')


class TerminateAllOtherSessionsView(LoginRequiredMixin, View):
    """
    Revokes all sessions except current.
    """
    def post(self, request):
        current_key = request.session.session_key
        count = SessionManagementService.terminate_all_other_sessions(request.user, current_key)
        messages.success(request, f"Terminated {count} other active session(s).")
        return redirect('accounts:sessions')


class ToggleFollowUserView(LoginRequiredMixin, View):
    """
    AJAX or form view to follow/unfollow other users.
    """
    def post(self, request, username):
        target_user = get_object_or_404(User, username=username)
        is_now_following = ProfileService.toggle_follow_user(request.user, target_user)
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            followers_count = UserFollow.objects.filter(following=target_user).count()
            return JsonResponse({
                'success': True,
                'is_following': is_now_following,
                'followers_count': followers_count
            })

        if is_now_following:
            messages.success(request, f"You are now following {target_user.username}.")
        else:
            messages.info(request, f"You have unfollowed {target_user.username}.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('accounts:profile', args=[username])))
