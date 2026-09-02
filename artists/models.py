"""
Artist Platform Models: Profiles, Band Members, Payout Accounts,
Verification Workflows, Royalty Statements, and Discography Relations.
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify


class VerificationStatus(models.TextChoices):
    UNVERIFIED = 'unverified', 'Unverified Creator'
    PENDING = 'pending', 'Verification Under Review'
    VERIFIED = 'verified', 'Verified Artist ✓'
    REJECTED = 'rejected', 'Verification Declined'


class Artist(models.Model):
    """
    Primary musical identity profile for solo creators, bands, and ensembles.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='artist_profile',
        help_text='Primary user account that owns and manages this artist page.'
    )
    name = models.CharField(max_length=150, unique=True, db_index=True)
    slug = models.SlugField(max_length=180, unique=True, db_index=True)
    stage_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    genres = models.CharField(max_length=255, blank=True, help_text='Comma-separated genres')
    country_of_origin = models.CharField(max_length=100, blank=True, default='Global')
    
    avatar = models.ImageField(upload_to='artists/avatars/%Y/%m/', blank=True, null=True)
    header_banner = models.ImageField(upload_to='artists/banners/%Y/%m/', blank=True, null=True)
    
    # Listener Metrics
    monthly_listeners = models.PositiveIntegerField(default=0, db_index=True)
    total_streams = models.PositiveBigIntegerField(default=0, db_index=True)
    follower_count = models.PositiveIntegerField(default=0, db_index=True)
    
    # Verification & Tier
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED,
        db_index=True
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # Financial Balances & Royalties
    unpaid_balance = models.DecimalField(max_digits=12, decimal_places=4, default=0.0000)
    total_paid_out = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    royalty_split_rate = models.DecimalField(max_digits=5, decimal_places=4, default=0.0045, help_text='USD per stream')
    
    # Social Handles & Streaming IDs
    website = models.URLField(blank=True)
    spotify_id = models.CharField(max_length=100, blank=True)
    soundcloud_id = models.CharField(max_length=100, blank=True)
    youtube_channel = models.URLField(blank=True)
    instagram_handle = models.CharField(max_length=100, blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    
    # Pinned Showcase Song
    pinned_song = models.ForeignKey('music.Song', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-monthly_listeners', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_verified_artist(self):
        return self.verification_status == VerificationStatus.VERIFIED

    @property
    def avatar_display(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return f"https://api.dicebear.com/7.x/initials/svg?seed={self.name}"

    @property
    def banner_display(self):
        if self.header_banner and hasattr(self.header_banner, 'url'):
            return self.header_banner.url
        return 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=1200&auto=format&fit=crop&q=80'


class ArtistMember(models.Model):
    """
    Individual band members and instrumentalists in a group artist profile.
    """
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='members')
    name = models.CharField(max_length=120)
    role_instrument = models.CharField(max_length=120, help_text='e.g. Lead Vocals, Bass, Keyboards')
    joined_year = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.role_instrument}) — {self.artist.name}"


class ArtistVerificationRequest(models.Model):
    """
    Formal application submitted by artists to receive blue checkmark verification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='verification_requests')
    legal_name = models.CharField(max_length=150)
    official_id_document = models.FileField(upload_to='verification_docs/%Y/%m/', blank=True, null=True)
    social_proof_links = models.TextField(help_text='Links to official Instagram, Spotify for Artists, Twitter, or Website')
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_verifications'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Verification for {self.artist.name} [{self.status}]"


class PayoutAccount(models.Model):
    """
    Bank account, Stripe Connect, or PayPal account for artist royalty distribution.
    """
    ACCOUNT_TYPE_CHOICES = (
        ('stripe_connect', 'Stripe Direct Bank Transfer'),
        ('paypal', 'PayPal MassPay Account'),
        ('wire_iban', 'International Wire Transfer (IBAN/SWIFT)'),
    )
    artist = models.OneToOneField(Artist, on_delete=models.CASCADE, related_name='payout_account')
    account_type = models.CharField(max_length=30, choices=ACCOUNT_TYPE_CHOICES, default='stripe_connect')
    account_identifier = models.CharField(max_length=150, help_text='Stripe Account ID, PayPal Email, or IBAN')
    beneficiary_name = models.CharField(max_length=150)
    currency = models.CharField(max_length=3, default='USD')
    is_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payout ({self.account_type}) for {self.artist.name}"


class RoyaltyStatement(models.Model):
    """
    Monthly calculated royalty earnings statement for artists.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='royalty_statements')
    period_start = models.DateField()
    period_end = models.DateField()
    total_streams = models.PositiveIntegerField(default=0)
    gross_earnings_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    platform_fee_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    net_payable_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_start']

    def __str__(self):
        return f"Statement {self.period_start} for {self.artist.name}: ${self.net_payable_usd}"


class ArtistFollower(models.Model):
    """
    Connects listener accounts to artists they follow.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='followed_artists')
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'artist')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} follows {self.artist.name}"
