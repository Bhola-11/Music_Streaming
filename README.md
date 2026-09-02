# Music_Streaming — MusicVerse Platform

🎵 Next-Gen Music Streaming & Artist Ecosystem built with Django MVT, Three.js 3D Visualizers, and Web Audio API.

## Architecture
- **Framework**: Django 5.0 (MVT Architecture)
- **Database**: SQLite (Local Dev) / PostgreSQL (Production)
- **Caching & Broker**: Redis & Celery
- **Audio Processing**: Mutagen, Waveform Peaks Generator, HTTP 206 Partial Content Range Streaming
- **3D & Visuals**: Three.js WebGL Particle Mesh, Dynamic Neon Shaders, Glassmorphic UI

## 14 Decoupled Applications
1. `accounts` — User auth, 2FA (TOTP), Session tracking, Social auth (Spotify/Google)
2. `audit` — Tamper-evident SHA-256 audit logging & threat anomaly detection
3. `artists` — Artist profile, creator studio, verification workflow, royalties
4. `music` — Tracks, lossless/MP3 audio formats, ID3 metadata parser, waveforms, synced lyrics
5. `albums` — Discography, LP/EP/Singles, track listings, artwork
6. `playlists` — Smart & collaborative playlists, drag-and-drop reordering
7. `player` — Web Audio API persistent player, queue manager, listening history
8. `discovery` — Trending charts, new releases, genre exploration, smart search
9. `recommendations` — Hybrid content-based & collaborative filtering algorithms
10. `subscriptions` — Free vs Pro Hi-Fi tiers, feature gates
11. `payments` — Stripe/PayPal abstraction, transaction logs, PDF invoice generator
12. `notifications` — Real-time in-app alerts and email notifications
13. `analytics` — Listener trends, artist revenue charts, platform telemetry
14. `moderation` — DMCA copyright takedowns, content reporting queues

## Quickstart
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply migrations
python manage.py migrate

# 3. Seed demo data (admin, artists, genres, plans)
python manage.py seed_demo_data

# 4. Start development server
python manage.py runserver
```
