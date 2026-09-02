"""
Asynchronous Celery tasks for account maintenance, session cleanup, and emails.
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import UserSession, User


@shared_task(name='accounts.tasks.cleanup_stale_sessions')
def cleanup_stale_sessions():
    """
    Deactivates and removes user session records older than 30 days.
    """
    threshold = timezone.now() - timezone.timedelta(days=30)
    stale_sessions = UserSession.objects.filter(last_activity__lt=threshold)
    count = stale_sessions.count()
    stale_sessions.delete()
    return f"Cleaned up {count} stale user sessions."


@shared_task(name='accounts.tasks.send_welcome_email')
def send_welcome_email(user_id: str):
    """
    Sends personalized welcome message to newly registered listener or creator.
    """
    user = User.objects.filter(id=user_id).first()
    if not user:
        return "User not found."

    subject = f"Welcome to MusicVerse, {user.username}!"
    body = (
        f"Hi {user.username},\n\n"
        f"Welcome to MusicVerse — where audio meets infinite space.\n"
        f"Start discovering top curated playlists, Hi-Fi lossless audio, and reactive 3D visualizers.\n\n"
        f"Explore now: http://localhost:8000/discovery/\n\n"
        f"— The MusicVerse Team"
    )
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True
    )
    return f"Welcome email queued for {user.email}"
