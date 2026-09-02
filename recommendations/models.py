import uuid
from django.db import models
from django.conf import settings

class RecommendationSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommendation_snapshots')
    recommended_song_ids = models.JSONField(default=list)
    algorithm_version = models.CharField(max_length=50, default='v1.0-hybrid')
    created_at = models.DateTimeField(auto_now_add=True)
