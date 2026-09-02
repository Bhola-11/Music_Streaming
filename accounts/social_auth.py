"""
OAuth2 and Social Provider Abstraction Layer.
Handles OAuth authentication flows for Spotify, Apple Music, Google, and Discord.
"""
import urllib.parse
import secrets
import requests
from django.conf import settings
from django.urls import reverse
from django.core.exceptions import ImproperlyConfigured
from .models import User, UserRole, UserProfile
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


class BaseOAuthProvider:
    """
    Abstract base provider handling state generation, authorization URL construction,
    and user token exchange.
    """
    provider_name = 'base'
    auth_endpoint = ''
    token_endpoint = ''
    userinfo_endpoint = ''
    default_scopes = []

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        self.client_id = client_id or getattr(settings, f'{self.provider_name.upper()}_CLIENT_ID', 'mock-client-id')
        self.client_secret = client_secret or getattr(settings, f'{self.provider_name.upper()}_CLIENT_SECRET', 'mock-secret')
        self.redirect_uri = redirect_uri or f"http://localhost:8000/accounts/oauth/callback/{self.provider_name}/"

    def get_authorization_url(self, state: str = None) -> tuple:
        if not state:
            state = secrets.token_urlsafe(32)

        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.default_scopes),
            'state': state,
        }
        encoded_query = urllib.parse.urlencode(params)
        return f"{self.auth_endpoint}?{encoded_query}", state

    def exchange_code_for_token(self, code: str) -> dict:
        """
        Exchanges authorization code for access and refresh tokens.
        """
        payload = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }
        try:
            response = requests.post(self.token_endpoint, data=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {'error': f"Failed token exchange: status {response.status_code}", 'details': response.text}
        except Exception as exc:
            return {'error': str(exc)}

    def fetch_user_profile(self, access_token: str) -> dict:
        """
        Retrieves user info from third-party provider API.
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        try:
            response = requests.get(self.userinfo_endpoint, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {'error': f"Failed user info fetch: {response.status_code}"}
        except Exception as exc:
            return {'error': str(exc)}


class SpotifyOAuthProvider(BaseOAuthProvider):
    """
    Spotify OAuth2 integration for syncing playlists and artist profiles.
    """
    provider_name = 'spotify'
    auth_endpoint = 'https://accounts.spotify.com/authorize'
    token_endpoint = 'https://accounts.spotify.com/api/token'
    userinfo_endpoint = 'https://api.spotify.com/v1/me'
    default_scopes = ['user-read-email', 'user-read-private', 'playlist-read-private', 'user-library-read']


class GoogleOAuthProvider(BaseOAuthProvider):
    """
    Google Identity OAuth2 provider.
    """
    provider_name = 'google'
    auth_endpoint = 'https://accounts.google.com/o/oauth2/v2/auth'
    token_endpoint = 'https://oauth2.googleapis.com/token'
    userinfo_endpoint = 'https://www.googleapis.com/oauth2/v3/userinfo'
    default_scopes = ['openid', 'email', 'profile']


class OAuthManager:
    """
    Resolves providers and orchestrates linking social accounts to MusicVerse users.
    """
    PROVIDERS = {
        'spotify': SpotifyOAuthProvider,
        'google': GoogleOAuthProvider,
    }

    @classmethod
    def get_provider(cls, name: str) -> BaseOAuthProvider:
        provider_cls = cls.PROVIDERS.get(name.lower())
        if not provider_cls:
            raise ValueError(f"Unsupported OAuth provider: {name}")
        return provider_cls()

    @classmethod
    def get_or_create_social_user(cls, provider_name: str, profile_data: dict) -> User:
        """
        Finds existing user by email or creates a new listener profile with social links.
        """
        email = profile_data.get('email')
        if not email:
            raise ValueError("Provider did not return an email address.")

        email = email.lower().strip()
        user = User.objects.filter(email=email).first()

        if not user:
            # Generate clean username
            raw_name = profile_data.get('name') or profile_data.get('display_name') or email.split('@')[0]
            clean_username = "".join(c for c in raw_name if c.isalnum() or c in ('_', '-'))[:25]
            if not clean_username or User.objects.filter(username=clean_username).exists():
                clean_username = f"{clean_username}_{secrets.token_hex(3)}"

            user = User.objects.create_user(
                email=email,
                username=clean_username,
                is_verified=True,
                role=UserRole.LISTENER
            )
            AuditService.log_action(
                action_type=f'auth.social_register.{provider_name}',
                category=ActionCategory.AUTHENTICATION,
                severity=ActionSeverity.INFO,
                user=user,
                description=f"User registered via {provider_name} OAuth"
            )

        return user
