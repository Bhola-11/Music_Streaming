"""
Custom Model Managers for Accounts.
"""
from django.contrib.auth.models import BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """
    Custom manager for MusicVerse User model where email is the primary identifier.
    """

    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        if not username:
            raise ValueError('The Username field must be set')

        email = self.normalize_email(email).lower()
        username = username.strip()
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'listener')

        user = self.model(email=email, username=username, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)

    def active_listeners(self):
        return self.filter(is_active=True, role='listener')

    def verified_artists(self):
        return self.filter(is_active=True, role='artist', is_verified=True)

    def premium_subscribers(self):
        return self.filter(is_active=True, is_premium=True)


class UserProfileManager(models.Manager):
    """
    Manager for profile queries and filtering by geography/onboarding.
    """

    def completed_profiles(self):
        return self.exclude(bio='').exclude(country='')
