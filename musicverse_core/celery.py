"""
Celery Configuration for MusicVerse
Handles asynchronous audio transcoding, waveform peak extraction,
recommendation batch runs, notification dispatching, and scheduled releases.
"""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'musicverse_core.settings')

app = Celery('musicverse')

app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'calculate-daily-trending-songs': {
        'task': 'discovery.tasks.calculate_trending_metrics',
        'schedule': crontab(minute=0, hour='*/4'),  # Every 4 hours
    },
    'generate-daily-personalized-mixes': {
        'task': 'recommendations.tasks.compute_user_recommendations',
        'schedule': crontab(minute=30, hour=3),  # Daily at 3:30 AM
    },
    'process-scheduled-track-releases': {
        'task': 'music.tasks.publish_scheduled_releases',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'aggregate-daily-artist-earnings': {
        'task': 'analytics.tasks.aggregate_daily_royalties',
        'schedule': crontab(minute=0, hour=1),  # Daily at 1:00 AM
    },
    'clean-expired-user-sessions': {
        'task': 'accounts.tasks.cleanup_stale_sessions',
        'schedule': crontab(minute=0, hour=0, day_of_week=0),  # Weekly Sunday midnight
    },
}

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard timeout for heavy audio processing
    worker_prefetch_multiplier=1,
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for verifying Celery connectivity."""
    print(f'MusicVerse Celery Worker Request: {self.request!r}')
