"""
Context processors for global template rendering across MusicVerse.
"""
from django.conf import settings


def musicverse_global_context(request):
    """
    Exposes platform configuration, active theme, subscription level, and user metadata.
    """
    context = {
        'PLATFORM_NAME': settings.MUSICVERSE_CONFIG.get('PLATFORM_NAME', 'MusicVerse'),
        'PLATFORM_TAGLINE': settings.MUSICVERSE_CONFIG.get('TAGLINE', 'Stream Beyond Dimensions'),
        'PLATFORM_VERSION': settings.MUSICVERSE_CONFIG.get('VERSION', '1.0.0'),
        'IS_PREMIUM_USER': False,
        'ACTIVE_THEME': 'dark-cosmic',
        'CURRENT_PATH': request.path,
    }

    if request.user.is_authenticated:
        # Check if user has active subscription
        context['IS_PREMIUM_USER'] = getattr(request.user, 'is_premium', False)
        if hasattr(request.user, 'preferences'):
            context['ACTIVE_THEME'] = request.user.preferences.theme or 'dark-cosmic'
        
        # Check if user is an artist
        context['IS_ARTIST'] = hasattr(request.user, 'artist_profile') and request.user.artist_profile is not None
        context['USER_ROLE'] = getattr(request.user, 'role', 'listener')
    else:
        context['IS_ARTIST'] = False
        context['USER_ROLE'] = 'anonymous'

    return context


def player_context(request):
    """
    Provides default player state configuration and audio visualizer preferences.
    """
    visualizer_mode = '3d-particle-mesh'
    audio_quality = 'standard'
    crossfade_enabled = False

    if request.user.is_authenticated and hasattr(request.user, 'preferences'):
        prefs = request.user.preferences
        visualizer_mode = prefs.visualizer_mode
        audio_quality = prefs.audio_quality
        crossfade_enabled = prefs.enable_crossfade

    return {
        'PLAYER_CONFIG': {
            'visualizer_mode': visualizer_mode,
            'audio_quality': audio_quality,
            'crossfade_enabled': crossfade_enabled,
            'default_volume': 0.85,
            'sample_rate': 44100,
        }
    }
