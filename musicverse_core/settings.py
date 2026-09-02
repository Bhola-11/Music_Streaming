"""
Django Settings for MusicVerse Platform.
Engineered for High-Performance Audio Streaming, Artist Dashboards & Realtime Interactions.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-musicverse-ultra-secure-key-9a8b7c6d5e4f3a2b1c0e9f8d7c6b5a4',
)

DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Application definition
DJANGO_CORE_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'rest_framework',
]

MUSICVERSE_APPS = [
    'accounts.apps.AccountsConfig',
    'audit.apps.AuditConfig',
    'artists.apps.ArtistsConfig',
    'music.apps.MusicConfig',
    'albums.apps.AlbumsConfig',
    'playlists.apps.PlaylistsConfig',
    'player.apps.PlayerConfig',
    'discovery.apps.DiscoveryConfig',
    'recommendations.apps.RecommendationsConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'payments.apps.PaymentsConfig',
    'notifications.apps.NotificationsConfig',
    'analytics.apps.AnalyticsConfig',
    'moderation.apps.ModerationConfig',
]

INSTALLED_APPS = DJANGO_CORE_APPS + THIRD_PARTY_APPS + MUSICVERSE_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'musicverse_core.middleware.RequestPerformanceMiddleware',
    'audit.middleware.AuditLoggingMiddleware',
    'accounts.middleware.UserActivityMiddleware',
]

ROOT_URLCONF = 'musicverse_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'musicverse_core.context_processors.musicverse_global_context',
                'musicverse_core.context_processors.player_context',
                'notifications.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'musicverse_core.wsgi.application'
ASGI_APPLICATION = 'musicverse_core.asgi.application'

# Database configuration
# Support PostgreSQL via DB_URL or fallback gracefully to SQLite for local development/testing
DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite')

if DB_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'musicverse_db'),
            'USER': os.getenv('DB_USER', 'musicverse_user'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'securepassword123'),
            'HOST': os.getenv('DB_HOST', 'localhost'),
            'PORT': os.getenv('DB_PORT', '5432'),
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images, 3D Assets)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (Audio files, Stems, Waveforms, Album Covers, Artist Avatars)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 1209600  # 2 weeks in seconds
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Caching Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'musicverse-cache',
        'TIMEOUT': 300,
    }
}

# Celery Broker & Results
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

# Music Streaming & Audio Settings
MUSICVERSE_CONFIG = {
    'PLATFORM_NAME': 'MusicVerse',
    'TAGLINE': 'Stream Beyond Dimensions',
    'VERSION': '1.0.0-PROD',
    'DEFAULT_AUDIO_BITRATE': 320,  # kbps
    'PREMIUM_AUDIO_BITRATE': 1411,  # Lossless FLAC kbps
    'FREE_STREAM_MAX_DURATION_SECONDS': 0,  # 0 means full song supported with standard quality
    'MAX_UPLOAD_SIZE_BYTES': 150 * 1024 * 1024,  # 150 MB max song upload
    'ALLOWED_AUDIO_EXTENSIONS': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'],
    'ALLOWED_IMAGE_EXTENSIONS': ['jpg', 'jpeg', 'png', 'webp'],
    'WAVEFORM_SAMPLE_POINTS': 120,
    'ROYALTY_RATE_PER_STREAM': 0.0045,  # $0.0045 per stream
    'ARTIST_PAYOUT_THRESHOLD': 50.00,  # $50 minimum payout
    'FREE_TIER_MAX_PLAYLISTS': 10,
    'PREMIUM_TIER_MAX_PLAYLISTS': 9999,
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Email Backend (Console in development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'support@musicverse.io'
