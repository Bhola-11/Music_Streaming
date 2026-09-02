"""
Forms for Accounts, Authentication, Profile & Security Settings.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, UserPreferences, AudioQuality, VisualizerMode, SecurityQuestion, UserRole
from .validators import ComplexPasswordValidator

User = get_user_model()


class UserRegistrationForm(forms.ModelForm):
    """
    User registration form enforcing email uniqueness, username validation,
    and strong password criteria.
    """
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input-glass',
            'placeholder': 'Create a secure password',
            'autocomplete': 'new-password'
        }),
        validators=[ComplexPasswordValidator().validate],
        help_text=_('Must be 8+ chars with uppercase, lowercase, numbers, and symbols.')
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input-glass',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password'
        }),
        label=_('Confirm Password')
    )
    account_type = forms.ChoiceField(
        choices=[(UserRole.LISTENER, 'Music Listener / Enthusiast'), (UserRole.ARTIST, 'Music Artist / Creator')],
        initial=UserRole.LISTENER,
        widget=forms.RadioSelect(attrs={'class': 'form-radio-glass'})
    )
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        label=_('I agree to the MusicVerse Terms of Service and Privacy Policy.')
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'account_type')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'e.g. cosmic_listener'}),
            'email': forms.EmailInput(attrs={'class': 'form-input-glass', 'placeholder': 'e.g. alex@musicverse.io'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email').lower().strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('An account with this email address already exists.'))
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('password_confirm')
        if p1 and p2 and p1 != p2:
            self.add_error('password_confirm', _('Passwords do not match.'))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.role = self.cleaned_data.get('account_type', UserRole.LISTENER)
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    """
    Login form for email and password authentication.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-input-glass',
            'placeholder': 'Enter your registered email',
            'autocomplete': 'username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input-glass',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        label=_('Remember this device for 30 days')
    )


class UserProfileForm(forms.ModelForm):
    """
    Profile editing form for biographical data, avatar, banner, and social handles.
    """
    first_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Last Name'})
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': '+1234567890'})
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-file-glass', 'accept': 'image/*'})
    )
    header_banner = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-file-glass', 'accept': 'image/*'})
    )

    # Social Media URL Fields
    twitter_url = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-input-glass', 'placeholder': 'https://x.com/username'}))
    instagram_url = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-input-glass', 'placeholder': 'https://instagram.com/username'}))
    spotify_url = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-input-glass', 'placeholder': 'https://open.spotify.com/artist/...'}))
    soundcloud_url = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-input-glass', 'placeholder': 'https://soundcloud.com/...'}))

    class Meta:
        model = UserProfile
        fields = ('headline', 'bio', 'location', 'country', 'website', 'is_public', 'show_listening_activity')
        widgets = {
            'headline': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'e.g. Electronic Sound Producer & Audiophile'}),
            'bio': forms.Textarea(attrs={'class': 'form-input-glass', 'rows': 4, 'placeholder': 'Describe your sonic journey...'}),
            'location': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'City, State'}),
            'country': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Country'}),
            'website': forms.URLInput(attrs={'class': 'form-input-glass', 'placeholder': 'https://yourwebsite.com'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'show_listening_activity': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['phone'].initial = user.phone
        
        # Populate social links
        if self.instance and self.instance.social_links:
            social = self.instance.social_links
            self.fields['twitter_url'].initial = social.get('twitter', '')
            self.fields['instagram_url'].initial = social.get('instagram', '')
            self.fields['spotify_url'].initial = social.get('spotify', '')
            self.fields['soundcloud_url'].initial = social.get('soundcloud', '')


class UserPreferencesForm(forms.ModelForm):
    """
    Configures audio playback, 3D visualizers, equalizer presets, and themes.
    """
    class Meta:
        model = UserPreferences
        fields = (
            'audio_quality',
            'visualizer_mode',
            'equalizer_preset',
            'normalize_volume',
            'enable_crossfade',
            'crossfade_seconds',
            'gapless_playback',
            'theme',
            'email_on_new_release',
            'email_on_playlist_like',
            'email_newsletter'
        )
        widgets = {
            'audio_quality': forms.Select(attrs={'class': 'form-select-glass'}),
            'visualizer_mode': forms.Select(attrs={'class': 'form-select-glass'}),
            'equalizer_preset': forms.Select(
                choices=[
                    ('Flat', 'Flat (Natural / Accurate)'),
                    ('Bass Boost', 'Deep Bass Boost (Club & EDM)'),
                    ('Vocal', 'Vocal Enhancer (Acoustic & Podcasts)'),
                    ('Electronic', 'Electronic / Synth Neon'),
                    ('Rock', 'Rock / High Dynamics'),
                    ('Classical', 'Classical / High Definition'),
                ],
                attrs={'class': 'form-select-glass'}
            ),
            'normalize_volume': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'enable_crossfade': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'crossfade_seconds': forms.NumberInput(attrs={'class': 'form-input-glass', 'min': 1, 'max': 12}),
            'gapless_playback': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'theme': forms.Select(
                choices=[
                    ('dark-cosmic', 'Cosmic Void (Deep Space & Violet)'),
                    ('neon-cyber', 'Neon Cyber (Cyan & Magenta)'),
                    ('synthwave', 'Synthwave Sunset (Amber & Neon)'),
                    ('obsidian', 'Obsidian Minimal (Pure Monochrome)'),
                ],
                attrs={'class': 'form-select-glass'}
            ),
            'email_on_new_release': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'email_on_playlist_like': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'email_newsletter': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        }


class TwoFactorVerifyForm(forms.Form):
    """
    Form for validating TOTP tokens or backup codes.
    """
    code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input-glass text-center tracking-widest text-2xl font-mono',
            'placeholder': '000000',
            'maxlength': '20',
            'autocomplete': 'one-time-code',
            'autofocus': True
        }),
        help_text=_('Enter the 6-digit code from your authenticator app or an 8-character backup code.')
    )


class SecurityQuestionForm(forms.Form):
    """
    Configures security questions.
    """
    question = forms.ChoiceField(
        choices=[
            ('first_concert', 'What was the first music concert you attended?'),
            ('favorite_instrument', 'What was your favorite musical instrument as a child?'),
            ('first_album', 'What was the first album you ever purchased or streamed?'),
            ('childhood_street', 'What was the name of the street you grew up on?'),
            ('first_pet', 'What was the name of your first pet?'),
        ],
        widget=forms.Select(attrs={'class': 'form-select-glass'})
    )
    answer = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input-glass', 'placeholder': 'Your secret answer'})
    )
