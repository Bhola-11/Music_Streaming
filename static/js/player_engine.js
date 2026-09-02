/**
 * MusicVerse 3D Audio Player Engine & Web Audio API Visualizer
 * Supports HTML5 Audio, Web Audio AnalyserNode, Gapless/Continuous Playback,
 * Up Next Queues, Shuffle/Repeat, Synced LRC Lyrics, and Playback Telemetry.
 */

class MusicVersePlayer {
    constructor() {
        this.audio = new Audio();
        this.audio.crossOrigin = "anonymous";
        this.queue = [];
        this.currentIndex = -1;
        this.isPlaying = false;
        this.isShuffled = false;
        this.repeatMode = 'off'; // 'off' | 'all' | 'one'
        this.currentSong = null;
        this.syncedLyrics = [];
        this.currentLyricIndex = -1;

        // Audio Context & Analyser for visualizers
        this.audioCtx = null;
        this.analyser = null;
        this.sourceNode = null;
        this.frequencyData = null;

        // Telemetry
        this.playbackStartTime = 0;
        this.secondsListened = 0;

        this.initElements();
        this.bindEvents();
    }

    initElements() {
        this.playBtn = document.getElementById('player-play-btn');
        this.prevBtn = document.getElementById('player-prev-btn');
        this.nextBtn = document.getElementById('player-next-btn');
        this.shuffleBtn = document.getElementById('player-shuffle-btn');
        this.repeatBtn = document.getElementById('player-repeat-btn');
        this.likeBtn = document.getElementById('player-like-btn');
        
        this.progressBar = document.getElementById('player-progress');
        this.progressFill = document.getElementById('player-progress-fill');
        this.currentTimeEl = document.getElementById('player-current-time');
        this.durationTimeEl = document.getElementById('player-duration-time');

        this.volumeSlider = document.getElementById('player-volume');
        this.volumeIcon = document.getElementById('player-volume-icon');

        this.coverEl = document.getElementById('player-cover');
        this.titleEl = document.getElementById('player-title');
        this.artistEl = document.getElementById('player-artist');
        this.playerBar = document.getElementById('musicverse-player-bar');

        this.visualizerCanvas = document.getElementById('player-visualizer-canvas');
        if (this.visualizerCanvas) {
            this.canvasCtx = this.visualizerCanvas.getContext('2d');
        }
    }

    initAudioContext() {
        if (!this.audioCtx) {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            if (AudioContextClass) {
                this.audioCtx = new AudioContextClass();
                this.analyser = this.audioCtx.createAnalyser();
                this.analyser.fftSize = 64;
                this.frequencyData = new Uint8Array(this.analyser.frequencyBinCount);
                try {
                    this.sourceNode = this.audioCtx.createMediaElementSource(this.audio);
                    this.sourceNode.connect(this.analyser);
                    this.analyser.connect(this.audioCtx.destination);
                    this.startVisualizerLoop();
                } catch (e) {
                    console.warn("Web Audio source already connected or blocked:", e);
                }
            }
        }
    }

    bindEvents() {
        if (this.playBtn) this.playBtn.addEventListener('click', () => this.togglePlay());
        if (this.prevBtn) this.prevBtn.addEventListener('click', () => this.previous());
        if (this.nextBtn) this.nextBtn.addEventListener('click', () => this.next());
        if (this.shuffleBtn) this.shuffleBtn.addEventListener('click', () => this.toggleShuffle());
        if (this.repeatBtn) this.repeatBtn.addEventListener('click', () => this.cycleRepeat());
        if (this.likeBtn) this.likeBtn.addEventListener('click', () => this.toggleLike());

        if (this.progressBar) {
            this.progressBar.addEventListener('click', (e) => this.seek(e));
        }

        if (this.volumeSlider) {
            this.volumeSlider.addEventListener('input', (e) => this.setVolume(e.target.value));
        }

        // Native audio element events
        this.audio.addEventListener('timeupdate', () => this.onTimeUpdate());
        this.audio.addEventListener('ended', () => this.onTrackEnded());
        this.audio.addEventListener('loadedmetadata', () => {
            if (this.durationTimeEl) {
                this.durationTimeEl.textContent = this.formatTime(this.audio.duration);
            }
        });
    }

    play(songData) {
        this.initAudioContext();
        if (this.audioCtx && this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }

        this.currentSong = songData;
        this.audio.src = songData.stream_url;
        this.audio.play().then(() => {
            this.isPlaying = true;
            this.updatePlayerUI();
            if (this.playerBar) this.playerBar.style.display = 'flex';
        }).catch(err => {
            console.error("Playback error:", err);
        });

        // Load synced lyrics
        this.fetchLyrics(songData.id);
    }

    togglePlay() {
        if (!this.audio.src) return;
        this.initAudioContext();

        if (this.isPlaying) {
            this.audio.pause();
            this.isPlaying = false;
        } else {
            this.audio.play();
            this.isPlaying = true;
        }
        this.updatePlayBtnUI();
    }

    next() {
        if (this.queue.length === 0) return;
        if (this.isShuffled) {
            this.currentIndex = Math.floor(Math.random() * this.queue.length);
        } else {
            this.currentIndex = (this.currentIndex + 1) % this.queue.length;
        }
        this.play(this.queue[this.currentIndex]);
    }

    previous() {
        if (this.audio.currentTime > 3) {
            this.audio.currentTime = 0;
            return;
        }
        if (this.queue.length === 0) return;
        this.currentIndex = (this.currentIndex - 1 + this.queue.length) % this.queue.length;
        this.play(this.queue[this.currentIndex]);
    }

    seek(e) {
        if (!this.audio.duration) return;
        const rect = this.progressBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const pct = clickX / rect.width;
        this.audio.currentTime = pct * this.audio.duration;
    }

    setVolume(val) {
        this.audio.volume = val / 100;
        if (this.volumeIcon) {
            this.volumeIcon.textContent = val == 0 ? '🔇' : (val < 50 ? '🔉' : '🔊');
        }
    }

    toggleShuffle() {
        this.isShuffled = !this.isShuffled;
        if (this.shuffleBtn) {
            this.shuffleBtn.style.color = this.isShuffled ? 'var(--accent-cyan)' : 'var(--text-dim)';
        }
    }

    cycleRepeat() {
        if (this.repeatMode === 'off') {
            this.repeatMode = 'all';
            this.repeatBtn.style.color = 'var(--accent-cyan)';
            this.repeatBtn.title = 'Repeat All';
        } else if (this.repeatMode === 'all') {
            this.repeatMode = 'one';
            this.repeatBtn.style.color = 'var(--accent-purple)';
            this.repeatBtn.title = 'Repeat One';
        } else {
            this.repeatMode = 'off';
            this.repeatBtn.style.color = 'var(--text-dim)';
            this.repeatBtn.title = 'Repeat Off';
        }
    }

    onTimeUpdate() {
        if (!this.audio.duration) return;
        const curr = this.audio.currentTime;
        const dur = this.audio.duration;
        const pct = (curr / dur) * 100;

        if (this.progressFill) this.progressFill.style.width = pct + '%';
        if (this.currentTimeEl) this.currentTimeEl.textContent = this.formatTime(curr);

        // Update synced lyrics line
        if (this.syncedLyrics && this.syncedLyrics.length > 0) {
            for (let i = this.syncedLyrics.length - 1; i >= 0; i--) {
                if (curr >= this.syncedLyrics[i].time) {
                    if (this.currentLyricIndex !== i) {
                        this.currentLyricIndex = i;
                        this.renderActiveLyric(this.syncedLyrics[i].text);
                    }
                    break;
                }
            }
        }
    }

    onTrackEnded() {
        this.recordTelemetry();
        if (this.repeatMode === 'one') {
            this.audio.currentTime = 0;
            this.audio.play();
        } else if (this.repeatMode === 'all' || this.currentIndex < this.queue.length - 1) {
            this.next();
        } else {
            this.isPlaying = false;
            this.updatePlayBtnUI();
        }
    }

    fetchLyrics(songId) {
        fetch(`/music/lyrics/${songId}/`)
            .then(res => res.json())
            .then(data => {
                if (data.has_lyrics && data.is_synced && data.synced) {
                    this.syncedLyrics = data.synced;
                } else {
                    this.syncedLyrics = [];
                }
            })
            .catch(() => { this.syncedLyrics = []; });
    }

    renderActiveLyric(text) {
        const lyricEl = document.getElementById('player-synced-lyric-bar');
        if (lyricEl) {
            lyricEl.textContent = text;
            lyricEl.style.opacity = '1';
        }
    }

    toggleLike() {
        if (!this.currentSong) return;
        fetch(`/player/api/favorite/${this.currentSong.id}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(res => res.json())
        .then(data => {
            if (data.success && this.likeBtn) {
                this.likeBtn.textContent = data.is_favorite ? '❤️' : '🤍';
            }
        });
    }

    recordTelemetry() {
        if (!this.currentSong) return;
        const dur = this.audio.duration || 180;
        const listened = Math.min(dur, Math.floor(this.audio.currentTime));
        const pct = (listened / dur) * 100;

        fetch(`/player/api/history/${this.currentSong.id}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({
                seconds_played: listened,
                completion_pct: pct,
                was_skipped: pct < 40
            })
        });
    }

    startVisualizerLoop() {
        const render = () => {
            requestAnimationFrame(render);
            if (!this.analyser || !this.canvasCtx || !this.isPlaying) return;

            this.analyser.getByteFrequencyData(this.frequencyData);
            const ctx = this.canvasCtx;
            const w = this.visualizerCanvas.width;
            const h = this.visualizerCanvas.height;

            ctx.clearRect(0, 0, w, h);
            const barCount = 24;
            const barWidth = w / barCount;

            for (let i = 0; i < barCount; i++) {
                const val = this.frequencyData[i] || 0;
                const barHeight = (val / 255) * h;
                const gradient = ctx.createLinearGradient(0, h, 0, 0);
                gradient.addColorStop(0, '#00C3FF');
                gradient.addColorStop(1, '#9D4EDD');
                ctx.fillStyle = gradient;
                ctx.fillRect(i * barWidth, h - barHeight, barWidth - 1, barHeight);
            }
        };
        render();
    }

    updatePlayerUI() {
        if (this.currentSong) {
            if (this.titleEl) this.titleEl.textContent = this.currentSong.title;
            if (this.artistEl) this.artistEl.textContent = this.currentSong.artist;
            if (this.coverEl) this.coverEl.src = this.currentSong.cover_art;
        }
        this.updatePlayBtnUI();
    }

    updatePlayBtnUI() {
        if (this.playBtn) {
            this.playBtn.innerHTML = this.isPlaying ? '❚❚' : '▶';
        }
    }

    formatTime(sec) {
        if (isNaN(sec)) return '0:00';
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    getCsrfToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? match[1] : '';
    }
}

// Global instance
window.musicPlayer = new MusicVersePlayer();

// Global play function accessible anywhere in templates
window.playSong = function(id, title, artist, cover_art, stream_url) {
    window.musicPlayer.play({ id, title, artist, cover_art, stream_url });
    // Append to active queue if not present
    const exists = window.musicPlayer.queue.some(s => s.id === id);
    if (!exists) {
        window.musicPlayer.queue.push({ id, title, artist, cover_art, stream_url });
        window.musicPlayer.currentIndex = window.musicPlayer.queue.length - 1;
    }
};
