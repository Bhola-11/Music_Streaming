"""
Authentication, Security, Two-Factor & Profile Services.
"""
import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
from django.contrib.auth import authenticate, login
from django.contrib.sessions.models import Session
from django.utils import timezone
from .models import User, UserProfile, UserPreferences, TwoFactorAuth, UserSession, UserFollow, UserRole
from audit.services import AuditService
from audit.models import ActionCategory, ActionSeverity


class AuthenticationService:
    """
    Manages account login, brute-force locking heuristics, and password operations.
    """

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    @classmethod
    def authenticate_user(cls, request, email, password):
        """
        Authenticates user with security checks for lockouts.
        """
        email = email.lower().strip()
        user_match = User.objects.filter(email=email).first()

        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
        if ',' in ip:
            ip = ip.split(',')[0].strip()

        if user_match and user_match.is_locked:
            if user_match.lock_expires_at and timezone.now() > user_match.lock_expires_at:
                # Unlock user
                user_match.is_locked = False
                user_match.failed_login_attempts = 0
                user_match.lock_expires_at = None
                user_match.save(update_fields=['is_locked', 'failed_login_attempts', 'lock_expires_at'])
            else:
                AuditService.log_security_event(
                    event_type='locked_account_login_attempt',
                    severity=ActionSeverity.HIGH,
                    user=user_match,
                    source_ip=ip,
                    details={'email': email}
                )
                return None, "Account is temporarily locked due to excessive failed attempts. Please try again later."

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if not user.is_active:
                return None, "This account is currently deactivated. Please contact support."

            # Reset failed attempts
            user.failed_login_attempts = 0
            user.last_login_ip = ip
            user.save(update_fields=['failed_login_attempts', 'last_login_ip'])
            return user, None
        else:
            if user_match:
                user_match.failed_login_attempts += 1
                if user_match.failed_login_attempts >= cls.MAX_FAILED_ATTEMPTS:
                    user_match.is_locked = True
                    user_match.lock_expires_at = timezone.now() + timezone.timedelta(minutes=cls.LOCKOUT_DURATION_MINUTES)
                    AuditService.log_security_event(
                        event_type='account_locked_excessive_failures',
                        severity=ActionSeverity.HIGH,
                        user=user_match,
                        source_ip=ip,
                        details={'failed_attempts': user_match.failed_login_attempts}
                    )
                user_match.save(update_fields=['failed_login_attempts', 'is_locked', 'lock_expires_at'])

            return None, "Invalid email or password."


class TwoFactorService:
    """
    TOTP (RFC 6238) generation and verification without heavy external dependencies.
    """

    @staticmethod
    def generate_secret() -> str:
        """Generates a random Base32 encoded 160-bit secret."""
        random_bytes = secrets.token_bytes(20)
        return base64.b32encode(random_bytes).decode('utf-8').replace('=', '')

    @staticmethod
    def generate_backup_codes(count: int = 8) -> list:
        """Generates a list of plain-text backup codes and their SHA-256 hashes."""
        plain_codes = []
        hashed_codes = []
        for _ in range(count):
            code = f"{secrets.token_hex(4)}-{secrets.token_hex(4)}".upper()
            plain_codes.append(code)
            hashed_codes.append(hashlib.sha256(code.encode('utf-8')).hexdigest())
        return plain_codes, hashed_codes

    @classmethod
    def get_totp_code(cls, secret_key: str, time_step: int = 30) -> str:
        """Computes current 6-digit TOTP token."""
        # Pad secret if necessary
        missing_padding = len(secret_key) % 8
        if missing_padding:
            secret_key += '=' * (8 - missing_padding)
        
        key = base64.b32decode(secret_key, casefold=True)
        intervals = int(time.time() // time_step)
        msg = struct.pack(">Q", intervals)
        h = hmac.new(key, msg, hashlib.sha1).digest()
        o = h[19] & 15
        h12 = (struct.unpack(">I", h[o:o + 4])[0] & 0x7fffffff) % 1000000
        return f"{h12:06d}"

    @classmethod
    def verify_totp(cls, secret_key: str, token_input: str) -> bool:
        """Validates TOTP token within a +/- 1 step time drift window."""
        token_input = token_input.strip()
        current_token = cls.get_totp_code(secret_key)
        if token_input == current_token:
            return True

        # Check drift (-30s, +30s)
        intervals = int(time.time() // 30)
        missing_padding = len(secret_key) % 8
        if missing_padding:
            padded_key = secret_key + '=' * (8 - missing_padding)
        else:
            padded_key = secret_key

        key = base64.b32decode(padded_key, casefold=True)
        for offset in (-1, 1):
            msg = struct.pack(">Q", intervals + offset)
            h = hmac.new(key, msg, hashlib.sha1).digest()
            o = h[19] & 15
            h12 = (struct.unpack(">I", h[o:o + 4])[0] & 0x7fffffff) % 1000000
            if f"{h12:06d}" == token_input:
                return True
        return False

    @classmethod
    def verify_and_consume_backup_code(cls, two_factor_obj: TwoFactorAuth, input_code: str) -> bool:
        """Verifies a backup code against hashed list and removes it if valid."""
        input_code = input_code.strip().upper()
        hashed_input = hashlib.sha256(input_code.encode('utf-8')).hexdigest()
        
        if hashed_input in two_factor_obj.backup_codes:
            two_factor_obj.backup_codes.remove(hashed_input)
            two_factor_obj.save(update_fields=['backup_codes'])
            return True
        return False


class SessionManagementService:
    """
    Handles user session listing and revocation across web and mobile endpoints.
    """

    @staticmethod
    def get_user_sessions(user: User):
        return UserSession.objects.filter(user=user, is_active=True).order_by('-last_activity')

    @staticmethod
    def terminate_session(user: User, session_key: str) -> bool:
        session_obj = UserSession.objects.filter(user=user, session_key=session_key).first()
        if session_obj:
            session_obj.is_active = False
            session_obj.save(update_fields=['is_active'])
            Session.objects.filter(session_key=session_key).delete()
            return True
        return False

    @staticmethod
    def terminate_all_other_sessions(user: User, current_session_key: str) -> int:
        other_sessions = UserSession.objects.filter(user=user, is_active=True).exclude(session_key=current_session_key)
        keys_to_delete = list(other_sessions.values_list('session_key', flat=True))
        
        count = other_sessions.update(is_active=False)
        Session.objects.filter(session_key__in=keys_to_delete).delete()
        return count


class ProfileService:
    """
    Social graph relations, profile updates, and follower management.
    """

    @staticmethod
    def toggle_follow_user(follower: User, target_user: User) -> bool:
        if follower == target_user:
            return False
        
        existing = UserFollow.objects.filter(follower=follower, following=target_user).first()
        if existing:
            existing.delete()
            return False  # Now unfollowed
        else:
            UserFollow.objects.create(follower=follower, following=target_user)
            return True  # Now following
