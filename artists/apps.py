"""
Artists App Configuration
"""
from django.apps import AppConfig


class ArtistsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'artists'
    verbose_name = 'Artist Platform & Creator Studio'
