"""
Complete Production & Catalog Demo Seeder for MusicVerse.
Populates Genres, Moods, Verified Artists, Master Albums, Sequenced Tracks,
Playlists, Charts, Hero Banners, Subscription Tiers, and Platform Telemetry.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from accounts.models import User, UserProfile, UserPreferences
from artists.models import Artist, VerificationStatus, PayoutAccount
from music.models import Genre, Mood, Song, Lyrics, TrackRating
from albums.models import Album, AlbumTrack, AlbumType
from playlists.models import Playlist, PlaylistTrack, PlaylistPrivacy
from discovery.models import FeaturedBanner, MusicChart, ChartEntry, TrendingMetric
from subscriptions.models import SubscriptionTier, SubscriptionBenefit
from recommendations.models import DailyMix, DailyMixTrack
from analytics.models import DailyPlatformMetric, StreamGeoHeatmap


class Command(BaseCommand):
    help = 'Seeds full production-grade music catalog and platform demo fixtures.'

    def handle(self, *args, **options):
        self.stdout.write("Seeding MusicVerse complete master catalog...")

        # 1. Admin & Demo Users
        admin_user, _ = User.objects.get_or_create(
            email='admin@musicverse.io',
            defaults={'username': 'admin', 'is_staff': True, 'is_superuser': True, 'role': 'label_admin'}
        )
        admin_user.set_password('admin12345')
        admin_user.save()

        listener, _ = User.objects.get_or_create(
            email='listener@musicverse.io',
            defaults={'username': 'audiophile', 'role': 'listener'}
        )
        listener.set_password('listener123')
        listener.save()
        UserPreferences.objects.get_or_create(user=listener, defaults={'enable_lossless': True, 'enable_3d_visualizer': True})

        # 2. Subscription Tiers
        tiers_data = [
            ('Free Listener', 'free', 'Standard 320kbps audio with basic features.', 0.00, 0.00, False, False),
            ('Hi-Fi Pro', 'hi-fi-pro', '1411kbps Lossless FLAC, 3D Spatial Audio & Zero Ads.', 9.99, 99.99, True, True),
            ('Creator Studio', 'creator-studio', 'Pro streaming + Artist Portal & Direct Uploads.', 19.99, 199.99, True, False),
            ('Family Master', 'family-master', 'Up to 6 accounts with full Hi-Fi lossless streaming.', 14.99, 149.99, True, False),
        ]
        for name, slug, desc, p_mo, p_yr, loss, pop in tiers_data:
            tier, _ = SubscriptionTier.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'description': desc,
                    'price_monthly_usd': Decimal(str(p_mo)),
                    'price_annual_usd': Decimal(str(p_yr)),
                    'allows_lossless': loss,
                    'is_popular': pop,
                }
            )
            SubscriptionBenefit.objects.get_or_create(tier=tier, benefit_text=f"{'1411 kbps Studio Master FLAC' if loss else '320 kbps Standard Audio'}")
            SubscriptionBenefit.objects.get_or_create(tier=tier, benefit_text="Unlimited Mobile & Desktop Web Streaming")

        # 3. Genres & Moods
        genres_data = [
            ('Synthwave', 'synthwave', '#FF2D7B', 'Neon retro-futuristic 80s synthesizers and cyber driving tracks.'),
            ('Cyberpunk', 'cyberpunk', '#00F5D4', 'Industrial dark electro, heavy basslines, and dystopian soundscapes.'),
            ('Lo-Fi Hip Hop', 'lo-fi', '#9D4EDD', 'Cozy chillhop beats, vintage vinyl crackle, and study sessions.'),
            ('Ambient Space', 'ambient', '#4361EE', 'Drifting cosmic pads, meditative frequencies, and zero-gravity drones.'),
            ('Techno & Acid', 'techno', '#FF9900', 'Raw analog kick drums, hypnotic modular pulses, and warehouse club energy.'),
            ('Orchestral Cinematic', 'cinematic', '#E63946', 'Epic symphonic film scores and monumental orchestral arrangements.'),
        ]
        genre_map = {}
        for name, slug, color, desc in genres_data:
            g, _ = Genre.objects.update_or_create(name=name, defaults={'slug': slug, 'color_hex': color, 'description': desc, 'is_featured': True})
            genre_map[slug] = g

        moods_data = [('Energetic', 'energetic', '⚡'), ('Chill & Focus', 'chill', '☕'), ('Dark & Moody', 'dark', '🌑'), ('Euphoric', 'euphoric', '✨')]
        for name, slug, icon in moods_data:
            Mood.objects.update_or_create(slug=slug, defaults={'name': name, 'icon': icon})

        # 4. Verified Artists
        artists_data = [
            ('Kavinsky Vector', 'kavinsky-vector', 'synthwave', 'France', 1420000, 8900000, 'Pioneer of analog synthwave and French electro driving soundscapes.'),
            ('Neon Valkyrie', 'neon-valkyrie', 'cyberpunk', 'Germany', 980000, 5600000, 'Industrial cyberpunk producer blending cyber modular synthesizers with dark techno.'),
            ('Celestial Drift', 'celestial-drift', 'ambient', 'Japan', 750000, 4200000, 'Tokyo ambient composer crafting generative meditative audio spaces.'),
            ('Coffee & Rhymes', 'coffee-rhymes', 'lo-fi', 'United States', 2100000, 14500000, 'Chillhop collective creating relaxing lo-fi vinyl beats for deep work.'),
        ]

        created_artists = []
        for name, slug, g_slug, country, listeners, streams, bio in artists_data:
            user_art, _ = User.objects.get_or_create(email=f"{slug}@musicverse.io", defaults={'username': slug, 'role': 'artist'})
            user_art.set_password('artist123')
            user_art.save()

            artist, _ = Artist.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'user': user_art,
                    'genres': genre_map[g_slug].name,
                    'country_of_origin': country,
                    'monthly_listeners': listeners,
                    'total_streams': streams,
                    'verification_status': VerificationStatus.VERIFIED,
                    'verified_at': timezone.now(),
                    'bio': bio,
                }
            )
            PayoutAccount.objects.get_or_create(artist=artist, defaults={'account_type': 'stripe', 'beneficiary_name': name, 'account_identifier': f"acct_{slug[:10]}"})
            created_artists.append(artist)

        # 5. Master Albums & Sequenced Songs
        albums_catalog = [
            (created_artists[0], 'Outrun Odyssey 2026', 'outrun-odyssey-2026', genre_map['synthwave'], [
                ('Nightcall Horizon', 245, 128, 'F# Minor'),
                ('Chrome Highway', 210, 130, 'A Minor'),
                ('Laser Sunset', 198, 126, 'D Minor'),
                ('Midnight Turbo', 234, 132, 'E Minor'),
            ]),
            (created_artists[1], 'Neo-Tokyo Overdrive', 'neo-tokyo-overdrive', genre_map['cyberpunk'], [
                ('Cybernetic Pulse', 260, 140, 'C Minor'),
                ('Ghost in the Silicon', 222, 138, 'G Minor'),
                ('Neural Uplink', 205, 142, 'B Minor'),
                ('Augmented Reality', 240, 135, 'F Minor'),
            ]),
            (created_artists[2], 'Interstellar Frequencies', 'interstellar-frequencies', genre_map['ambient'], [
                ('Andromeda Drift', 380, 75, 'C Major'),
                ('Starlight Echoes', 340, 70, 'G Major'),
                ('Solar Wind Meditation', 410, 65, 'D Major'),
            ]),
            (created_artists[3], 'Midnight Coffee Sessions', 'midnight-coffee-sessions', genre_map['lo-fi'], [
                ('Rain on the Window', 165, 85, 'Eb Major'),
                ('Late Night Thoughts', 178, 88, 'Ab Major'),
                ('Warm Sweater', 152, 82, 'Bb Major'),
            ]),
        ]

        all_songs = []
        for artist, alb_title, alb_slug, genre, track_list in albums_catalog:
            album, _ = Album.objects.update_or_create(
                slug=alb_slug,
                defaults={
                    'title': alb_title,
                    'artist': artist,
                    'album_type': AlbumType.LP,
                    'release_date': timezone.now().date() - timedelta(days=random.randint(10, 180)),
                    'description': f"Official studio album by {artist.name}.",
                    'is_published': True,
                }
            )

            for pos, (track_title, duration, bpm, key) in enumerate(track_list, start=1):
                # Simulated waveform peaks
                waveform = [round(0.2 + 0.6 * random.random(), 2) for _ in range(60)]
                song, _ = Song.objects.update_or_create(
                    slug=f"{artist.slug}-{track_title.lower().replace(' ', '-')}",
                    defaults={
                        'title': track_title,
                        'artist': artist,
                        'album': album,
                        'genre': genre,
                        'duration_seconds': duration,
                        'bitrate_kbps': 1411 if pos == 1 else 320,
                        'sample_rate_hz': 48000 if pos == 1 else 44100,
                        'bpm': bpm,
                        'musical_key': key,
                        'waveform_data': waveform,
                        'play_count': random.randint(5000, 120000),
                        'like_count': random.randint(300, 8500),
                        'is_premium_only': (pos == 1),
                        'is_published': True,
                    }
                )
                AlbumTrack.objects.update_or_create(album=album, track_number=pos, defaults={'song': song, 'disc_number': 1})
                all_songs.append(song)

                # Sample Lyrics
                Lyrics.objects.update_or_create(
                    song=song,
                    defaults={
                        'plain_lyrics': f"[Verse 1]\nNeon lights in the rain\nSynthesizer in my veins\n\n[Chorus]\nDriving through the night\nUnder the ultraviolet light\n\n[Outro]\nLost in the digital frequency.",
                        'writer_credit': artist.name,
                        'is_synced': True,
                        'synced_lyrics_json': [
                            {'time': 5.0, 'text': 'Neon lights in the rain'},
                            {'time': 12.0, 'text': 'Synthesizer in my veins'},
                            {'time': 24.0, 'text': 'Driving through the night'},
                            {'time': 32.0, 'text': 'Under the ultraviolet light'},
                        ]
                    }
                )

        # 6. Hero Banners & Official Charts
        FeaturedBanner.objects.update_or_create(
            title="Outrun Odyssey 2026",
            defaults={
                'subtitle': "Experience Kavinsky Vector's groundbreaking 1411 kbps studio master LP.",
                'badge_text': "EXCLUSIVE PRO RELEASE",
                'action_url': f"/albums/outrun-odyssey-2026/",
                'action_button_text': "Stream Studio Master",
                'is_active': True,
                'display_order': 1,
            }
        )

        chart, _ = MusicChart.objects.update_or_create(
            slug='top-50-global',
            defaults={'title': 'Top 50 Global Masters', 'description': 'The most streamed tracks worldwide on MusicVerse.'}
        )
        for rank, s in enumerate(all_songs[:10], start=1):
            ChartEntry.objects.update_or_create(chart=chart, song=s, defaults={'rank': rank, 'peak_rank': rank, 'weeks_on_chart': random.randint(1, 12)})

        # 7. Editorial Playlists
        pl, _ = Playlist.objects.update_or_create(
            slug='cyber-highways-curated',
            defaults={
                'title': 'Cyber Highways & Neon Nights',
                'owner': admin_user,
                'description': 'Editorial curated synthwave and dark electro for night driving.',
                'privacy': PlaylistPrivacy.PUBLIC,
                'is_featured_curated': True,
                'follower_count': 18400,
            }
        )
        for pos, s in enumerate(all_songs[:8], start=1):
            PlaylistTrack.objects.update_or_create(playlist=pl, song=s, defaults={'position': pos, 'added_by': admin_user})

        # 8. Analytics Rollup & Geo Heatmaps
        DailyPlatformMetric.objects.update_or_create(
            date=timezone.now().date(),
            defaults={
                'total_streams': 48920,
                'unique_listeners': 12400,
                'new_users_registered': 420,
                'new_tracks_uploaded': 18,
                'bandwidth_served_gb': Decimal('478.50'),
                'royalty_accrued_usd': Decimal('220.14'),
            }
        )

        countries = [('US', 'United States', 185000), ('DE', 'Germany', 94000), ('GB', 'United Kingdom', 87000), ('FR', 'France', 72000), ('JP', 'Japan', 68000)]
        for code, name, plays in countries:
            StreamGeoHeatmap.objects.update_or_create(country_code=code, defaults={'country_name': name, 'stream_count': plays, 'listener_count': plays // 3})

        self.stdout.write(self.style.SUCCESS("[OK] MusicVerse full production master catalog seeded successfully!"))
