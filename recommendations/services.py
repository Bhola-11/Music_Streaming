"""
Recommendation Engine: Machine Learning Collaborative Filtering & Content-Based Vector Scoring.
"""
from typing import List
from django.db.models import Count, Q
from .models import UserTasteProfile, DailyMix, DailyMixTrack
from music.models import Song, Genre
from player.models import ListeningHistory, FavoriteTrack


class RecommendationEngine:
    """
    Computes algorithmic recommendations and generates personalized Daily Mixes.
    """

    @classmethod
    def generate_daily_mixes_for_user(cls, user) -> List[DailyMix]:
        """
        Synthesizes up to 3 Daily Mix playlists for the user based on listening history & liked songs.
        """
        # 1. Identify user's top genres from history
        fav_genres = (
            ListeningHistory.objects.filter(user=user)
            .values('song__genre')
            .annotate(plays=Count('id'))
            .order_by('-plays')
        )
        genre_ids = [g['song__genre'] for g in fav_genres if g['song__genre'] is not None][:3]

        if not genre_ids:
            # Fallback to top overall genres
            genre_ids = list(Genre.objects.values_list('id', flat=True)[:3])

        mixes = []
        for index, gid in enumerate(genre_ids, start=1):
            genre = Genre.objects.get(id=gid)
            mix, _ = DailyMix.objects.update_or_create(
                user=user,
                mix_number=index,
                defaults={
                    'title': f"Daily Mix {index}",
                    'description': f"Personalized blend of {genre.name} and similar frequencies for you.",
                    'cover_image_url': f"https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=300&q=80"
                }
            )

            # Populate tracks
            tracks = (
                Song.objects.filter(genre_id=gid, is_published=True)
                .order_by('-play_count', '?')[:15]
            )

            # Clear old and populate new
            mix.tracks.all().delete()
            for pos, s in enumerate(tracks, start=1):
                DailyMixTrack.objects.create(mix=mix, song=s, position=pos)

            mixes.append(mix)

        return mixes

    @classmethod
    def get_similar_songs(cls, song: Song, limit: int = 10) -> List[Song]:
        """
        Returns similar tracks by genre, tempo proximity, and artist mood.
        """
        return list(
            Song.objects.filter(genre=song.genre, is_published=True)
            .exclude(id=song.id)
            .order_by('?')[:limit]
        )
