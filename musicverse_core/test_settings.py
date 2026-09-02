"""
Test-specific settings override for MusicVerse.
Replaces ManifestStaticFilesStorage with the default FileSystemStorage
to avoid 'Missing staticfiles manifest entry' errors when running tests
without first running `collectstatic`.
"""
from musicverse_core.settings import *  # noqa: F403

# Use simple static file storage in tests (no manifest hash needed)
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Disable whitenoise manifest storage during tests
WHITENOISE_MANIFEST_STRICT = False

# Speed up password hashing during tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
