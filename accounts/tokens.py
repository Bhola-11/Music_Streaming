"""
Cryptographic Token Generators for Account Verification & Secure Operations.
"""
import base64
import hashlib
import hmac
import time
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


class SecureTokenGenerator:
    """
    Time-sensitive HMAC cryptographic token generator for email verification,
    password resets, and media streaming access tokens.
    """
    def __init__(self, key_salt: str = 'musicverse.token.salt', validity_seconds: int = 86400):
        self.key_salt = key_salt
        self.validity_seconds = validity_seconds

    def _make_hash_value(self, user, timestamp: int) -> str:
        login_timestamp = ''
        if user.last_login:
            login_timestamp = user.last_login.replace(microsecond=0, tzinfo=None).isoformat()
        
        email_field = user.email or ''
        return f"{user.pk}{user.password}{login_timestamp}{timestamp}{email_field}{self.key_salt}"

    def make_token(self, user) -> str:
        """Generates a secure timestamped token string."""
        now_ts = int(time.time())
        hash_val = self._make_hash_value(user, now_ts)
        digest = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            hash_val.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Token format: <timestamp_hex>-<digest>
        ts_b36 = hex(now_ts)[2:]
        return f"{ts_b36}-{digest}"

    def check_token(self, user, token: str) -> bool:
        """Validates token authenticity and checks for expiration."""
        if not user or not token or '-' not in token:
            return False

        try:
            ts_b36, digest = token.split('-', 1)
            token_ts = int(ts_b36, 16)
        except (ValueError, TypeError):
            return False

        # Check expiration
        current_ts = int(time.time())
        if (current_ts - token_ts) > self.validity_seconds or (token_ts > current_ts + 60):
            return False

        expected_hash = self._make_hash_value(user, token_ts)
        expected_digest = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            expected_hash.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(digest, expected_digest)


# Singleton Instances
account_activation_token = SecureTokenGenerator(key_salt='musicverse.activation', validity_seconds=172800) # 48 hours
password_reset_token = SecureTokenGenerator(key_salt='musicverse.password_reset', validity_seconds=3600)   # 1 hour
streaming_access_token = SecureTokenGenerator(key_salt='musicverse.stream_auth', validity_seconds=7200)    # 2 hours
