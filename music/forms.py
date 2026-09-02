"""
Forms for Music Upload, Editing, Lyrics, and Comments.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Song, Lyrics, SongContributor, TrackComment, Genre, Mood
from .audio_processor import AudioMetadataExtractor, WaveformPeakGenerator


class SongUploadForm(forms.ModelForm):
    """
    Drag-and-drop or file selector upload form with automatic metadata extraction.
    """
    audio_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-file-glass', 'accept': '.mp3,.wav,.flac,.aac,.ogg,.m4a'})
    )
    cover_art = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-file-glass', 'accept': 'image/*'})
    )
    is_premium_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        label=_('Exclusive to Pro Hi-Fi Subscribers')
    )
    is_explicit = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        label=_('Contains Explicit Content')
    )

    class Meta:
        model = Song
        fields = (
            'title',
            'genre',
            'moods',
            'audio_file',
            'cover_art',
            'bpm',
            'musical_key',
            'is_explicit',
            'is_premium_only',
            'release_date',
            'isrc_code',
            'copyright_line',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Song Title'}),
            'genre': forms.Select(attrs={'class': 'form-select-glass'}),
            'moods': forms.SelectMultiple(attrs={'class': 'form-select-glass', 'style': 'height: 110px;'}),
            'bpm': forms.NumberInput(attrs={'class': 'form-input-glass', 'placeholder': 'e.g. 128'}),
            'musical_key': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'e.g. F# Minor'}),
            'release_date': forms.DateInput(attrs={'class': 'form-input-glass', 'type': 'date'}),
            'isrc_code': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'US-ABC-26-00001'}),
            'copyright_line': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': '© 2026 Artist Name'}),
        }

    def clean_audio_file(self):
        file = self.cleaned_data.get('audio_file')
        if file:
            ext = file.name.split('.')[-1].lower()
            allowed = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a']
            if ext not in allowed:
                raise ValidationError(_(f"Unsupported audio format .{ext}. Allowed: {', '.join(allowed)}"))
            # 150 MB max
            if file.size > 150 * 1024 * 1024:
                raise ValidationError(_("Audio file exceeds maximum 150 MB upload limit."))
        return file


class SongEditForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = (
            'title',
            'genre',
            'moods',
            'cover_art',
            'bpm',
            'musical_key',
            'is_explicit',
            'is_premium_only',
            'is_published',
            'copyright_line',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input-glass'}),
            'genre': forms.Select(attrs={'class': 'form-select-glass'}),
            'moods': forms.SelectMultiple(attrs={'class': 'form-select-glass'}),
            'bpm': forms.NumberInput(attrs={'class': 'form-input-glass'}),
            'musical_key': forms.TextInput(attrs={'class': 'form-input-glass'}),
            'copyright_line': forms.TextInput(attrs={'class': 'form-input-glass'}),
            'is_explicit': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'is_premium_only': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        }


class LyricsForm(forms.ModelForm):
    class Meta:
        model = Lyrics
        fields = ('plain_lyrics', 'writer_credit', 'is_synced')
        widgets = {
            'plain_lyrics': forms.Textarea(attrs={'class': 'form-input-glass', 'rows': 8, 'placeholder': 'Type full song lyrics here...'}),
            'writer_credit': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Lyricist credit'}),
            'is_synced': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        }


class TrackCommentForm(forms.ModelForm):
    class Meta:
        model = TrackComment
        fields = ('comment_text', 'timestamp_seconds')
        widgets = {
            'comment_text': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Leave a timestamped reaction...'}),
            'timestamp_seconds': forms.HiddenInput(),
        }
