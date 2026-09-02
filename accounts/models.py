"""
User and Profile Models for MusicVerse.
Implements custom User, UserProfile, UserPreferences, TwoFactorAuth,
SecurityQuestion, UserSession, UserFollow, and ArtistProfileLink.
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import UserManager, UserProfileManager
from .validators import validate_username_format, validate_phone_number, validate_image_file_extension, validate_image_file_size


class UserRole(models.TextChoices):
    LISTENER = 'listener', _('Standard Listener')
    ARTIST = 'artist', _('Verified Creator / Artist')
    MODERATOR = 'moderator', _('Content Moderator')
    ADMIN = 'admin', _('Platform Administrator')


class User(AbstractUser):
    """
    Custom primary User model for MusicVerse.
    Email acts as the unique login credential.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True, db_index=True)
    username = models.CharField(
        _('username'),
        max_length=35,
        unique=True,
        validators=[validate_username_format],
        db_index=True,
        help_text=_('Required. 3-35 characters. Letters, numbers, underscores, or hyphens.')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone_number],
        help_text=_('Optional international phone number for SMS alerts and account recovery.')
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.LISTENER,
        db_index=True
    )
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        validators=[validate_image_file_extension, validate_image_file_size]
    )
    
    # Flags & Tiers
    is_verified = models.BooleanField(default=False, help_text=_('Designates email or identity verification.'))
    is_premium = models.BooleanField(default=False, db_index=True, help_text=_('True if user holds an active premium tier.'))
    premium_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Creator & Storage Quotas
    storage_quota_bytes = models.BigIntegerField(default=524288000, help_text=_('Default 500 MB upload limit for artists'))
    storage_used_bytes = models.BigIntegerField(default=0)
    
    # Security tracking
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    lock_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Email is the username field for Django authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UserManager()

    class Meta:
        ordering = ['-date_joined']
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email', 'role']),
            models.Index(fields=['is_premium', 'is_active']),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"

    @property
    def full_name_or_username(self):
        name = self.get_full_name()
        return name if name else self.username

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        # Fallback to high-res SVG avatar
        return f"https://api.dicebear.com/7.x/identicon/svg?seed={self.username}"

    @property
    def is_artist_user(self):
        return self.role == UserRole.ARTIST or hasattr(self, 'artist_profile')

    @property
    def storage_usage_percentage(self):
        if self.storage_quota_bytes <= 0:
            return 0
        return round((self.storage_used_bytes / self.storage_quota_bytes) * 100, 1)


class UserProfile(models.Model):
    """
    Extended user profile for biographical details, public presence, and social profiles.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, max_length=1000, help_text=_('Tell the community about yourself and your taste.'))
    headline = models.CharField(max_length=150, blank=True, help_text=_('Short tagline displayed on profile header.'))
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=60, blank=True, default='United States')
    birth_date = models.DateField(null=True, blank=True)
    
    header_banner = models.ImageField(
        upload_to='banners/%Y/%m/',
        blank=True,
        null=True,
        validators=[validate_image_file_extension, validate_image_file_size]
    )
    
    # Social links structure
    social_links = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Dictionary containing twitter, instagram, soundcloud, spotify, youtube links')
    )
    
    # Public visibility flags
    is_public = models.BooleanField(default=True, help_text=_('Whether profile is publicly discoverable.'))
    show_listening_activity = models.BooleanField(default=True)
    show_public_playlists = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserProfileManager()

    def __str__(self):
        return f"Profile: {self.user.username}"


class AudioQuality(models.TextChoices):
    LOW = 'low', _('Data Saver (96 kbps)')
    STANDARD = 'standard', _('Standard High Quality (320 kbps MP3)')
    LOSSLESS = 'lossless', _('Hi-Fi Lossless (1411 kbps FLAC) - Premium Only')


class VisualizerMode(models.TextChoices):
    PARTICLE_MESH = '3d-particle-mesh', _('3D Cosmic Particle Mesh (Three.js)')
    NEON_BARS = 'neon-bars', _('Neon Cyber Frequency Bars')
    TUNNEL_VORTEX = 'tunnel-vortex', _('3D Warp Tunnel Visualizer')
    MINIMAL_WAVE = 'minimal-wave', _('Minimal Sine Waveform')
    OFF = 'off', _('Visualizer Disabled (Battery Saver)')


class UserPreferences(models.Model):
    """
    Stores streaming bitrate, visualizer, audio equalizer, and notification settings.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='preferences')
    
    # Audio Playback
    audio_quality = models.CharField(
        max_length=20,
        choices=AudioQuality.choices,
        default=AudioQuality.STANDARD
    )
    normalize_volume = models.BooleanField(default=True, help_text=_('ReplayGain audio normalization.'))
    enable_crossfade = models.BooleanField(default=False)
    crossfade_seconds = models.PositiveIntegerField(default=3)
    equalizer_preset = models.CharField(max_length=50, default='Flat')  # Flat, Bass Boost, Vocal, Electronic, Rock
    gapless_playback = models.BooleanField(default=True)
    
    # 3D Visualizer Preferences
    visualizer_mode = models.CharField(
        max_length=30,
        choices=VisualizerMode.choices,
        default=VisualizerMode.PARTICLE_MESH
    )
    visualizer_sensitivity = models.FloatField(default=1.0)
    visualizer_bloom_effect = models.BooleanField(default=True)
    
    # UI Theme
    theme = models.CharField(max_length=30, default='dark-cosmic')  # dark-cosmic, neon-cyber, synthwave, obsidian
    
    # Notifications
    email_on_new_release = models.BooleanField(default=True)
    email_on_playlist_like = models.BooleanField(default=True)
    email_on_artist_update = models.BooleanField(default=True)
    email_newsletter = models.BooleanField(default=False)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences: {self.user.username}"


class TwoFactorAuth(models.Model):
    """
    Stores TOTP secret and backup recovery codes for two-factor authentication.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_factor')
    secret_key = models.CharField(max_length=64, help_text=_('Base32 encoded TOTP secret key'))
    is_enabled = models.BooleanField(default=False)
    backup_codes = models.JSONField(default=list, help_text=_('List of one-time backup hash codes'))
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        status = 'Enabled' if self.is_enabled else 'Disabled'
        return f"2FA for {self.user.username} ({status})"


class SecurityQuestion(models.Model):
    """
    Security questions for secondary account recovery verification.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_questions')
    question = models.CharField(max_length=255)
    answer_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sec Question for {self.user.username}: {self.question}"


class UserSession(models.Model):
    """
    Tracks active devices and sessions for user account management and remote revocation.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=64, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    device_type = models.CharField(max_length=50, default='Desktop Browser')
    location_city = models.CharField(max_length=100, blank=True, default='Unknown')
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-last_activity']

    def __str__(self):
        return f"{self.user.username} on {self.device_type} ({self.ip_address})"


class UserFollow(models.Model):
    """
    Social graph model: users following other users or curator profiles.
    """
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_relations')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_relations')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        unique_together = ('follower', 'following')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.username} -> {self.following.username}"


class ArtistProfileLink(models.Model):
    """
    Associates a user account with an Artist entity, allowing team/band management roles.
    """
    ROLE_CHOICES = (
        ('owner', 'Primary Artist Owner'),
        ('manager', 'Artist Manager / Label Rep'),
        ('producer', 'Producer / Contributor'),
        ('member', 'Band Member'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='artist_memberships')
    artist = models.ForeignKey('artists.Artist', on_delete=models.CASCADE, related_name='user_memberships')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='owner')
    can_upload_music = models.BooleanField(default=True)
    can_manage_releases = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=True)
    can_withdraw_funds = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'artist')

    def __str__(self):
        return f"{self.user.username} ({self.role}) -> {self.artist.name}"
