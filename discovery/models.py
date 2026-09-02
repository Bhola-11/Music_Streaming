import uuid
from django.db import models


class TrendingSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot_date = models.DateField(auto_now_add=True, db_index=True)
    top_song_ids = models.JSONField(default=list)
    top_artist_ids = models.JSONField(default=list)
    top_album_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-snapshot_date']
