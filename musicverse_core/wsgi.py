"""
WSGI config for MusicVerse project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicverse_core.settings')

application = get_wsgi_application()
