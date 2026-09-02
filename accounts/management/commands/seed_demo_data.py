"""
Management command to seed initial genres, artists, sample songs, and plans.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from music.models import Genre, Song
from artists.models import Artist, VerificationStatus
from albums.models import Album, AlbumType
from subscriptions.models import SubscriptionPlan
from playlists.models import Playlist, PlaylistSong

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial demonstration data for MusicVerse platform'

    def handle(self, *args, **options):
        self.stdout.write("Seeding MusicVerse demo data...")

        # 1. Create Superuser / Admin
        admin_user, created = User.objects.get_or_create(
            email='admin@musicverse.io',
            defaults={
                'username': 'admin',
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
                'role': 'admin'
            }
        )
        if created:
            admin_user.set_password('AdminPass123!@#')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin: admin@musicverse.io / AdminPass123!@#"))

        # 2. Create Demo Listener
        listener_user, created = User.objects.get_or_create(
            email='listener@musicverse.io',
            defaults={
                'username': 'cosmic_listener',
                'is_premium': True,
                'is_verified': True,
                'role': 'listener'
            }
        )
        if created:
            listener_user.set_password('Listener123!@#')
            listener_user.save()
            self.stdout.write(self.style.SUCCESS("Created listener: listener@musicverse.io / Listener123!@#"))

        # 3. Create Demo Artist
        artist_user, created = User.objects.get_or_create(
            email='artist@musicverse.io',
            defaults={
                'username': 'aurora_pulse',
                'is_verified': True,
                'role': 'artist'
            }
        )
        if created:
            artist_user.set_password('Artist123!@#')
            artist_user.save()

        artist, _ = Artist.objects.get_or_create(
            user=artist_user,
            defaults={
                'name': 'Aurora Pulse',
                'bio': 'Pioneering ambient electronic soundscapes and deep cyber frequencies.',
                'genres': 'Synthwave, Ambient, Electronic',
                'verification_status': VerificationStatus.VERIFIED,
                'monthly_listeners': 48200,
                'total_streams': 324500,
            }
        )

        # 4. Create Genres
        genres_data = [
            ('Synthwave', '#00F5D4', 'Retro-futuristic 80s synthesizers and neon night drives.'),
            ('Cyberpunk EDM', '#F72585', 'High-energy basslines and holographic club rhythms.'),
            ('Deep Ambient', '#7B2CBF', 'Atmospheric drones and space meditation frequencies.'),
            ('Lo-Fi Hip Hop', '#F77F00', 'Relaxing beats to study, code, and relax.'),
            ('Hi-Fi Classical', '#4361EE', 'Acoustic symphony recordings preserved in full dynamic range.'),
        ]

        for name, color, desc in genres_data:
            Genre.objects.get_or_create(name=name, defaults={'color_hex': color, 'description': desc})

        # 5. Create Subscription Plans
        SubscriptionPlan.objects.get_or_create(
            slug='free',
            defaults={
                'name': 'Free Tier',
                'price_usd_monthly': 0.00,
                'price_usd_yearly': 0.00,
                'has_lossless_audio': False,
                'has_unlimited_skips': False,
                'has_offline_downloads': False,
                'features_list': ['Standard 320 kbps MP3 streaming', 'Ad-supported listening', 'Standard playlists']
            }
        )

        SubscriptionPlan.objects.get_or_create(
            slug='pro-hifi',
            defaults={
                'name': 'Pro Hi-Fi Master',
                'price_usd_monthly': 9.99,
                'price_usd_yearly': 99.99,
                'has_lossless_audio': True,
                'has_unlimited_skips': True,
                'has_offline_downloads': True,
                'features_list': ['1411 kbps Studio Master FLAC', 'Ad-free audio experience', 'Full 3D WebGL visualizers', 'Offline listening tokens', 'Exclusive artist releases']
            }
        )

        self.stdout.write(self.style.SUCCESS("MusicVerse seed data populated successfully!"))
