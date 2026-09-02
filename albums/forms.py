"""
Forms for Album Creation and Discography Management.
"""
from django import forms
from .models import Album, AlbumTrack, DiscEdition, AlbumReview, RecordLabel


class AlbumForm(forms.ModelForm):
    cover_art = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-file-glass', 'accept': 'image/*'})
    )

    class Meta:
        model = Album
        fields = (
            'title',
            'album_type',
            'record_label',
            'cover_art',
            'release_date',
            'upc_code',
            'description',
            'copyright_line',
            'is_explicit',
            'is_published',
        )
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Album Title'}),
            'album_type': forms.Select(attrs={'class': 'form-select-glass'}),
            'record_label': forms.Select(attrs={'class': 'form-select-glass'}),
            'release_date': forms.DateInput(attrs={'class': 'form-input-glass', 'type': 'date'}),
            'upc_code': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'e.g. 190295829102'}),
            'description': forms.Textarea(attrs={'class': 'form-input-glass', 'rows': 4, 'placeholder': 'Liner notes and album story...'}),
            'copyright_line': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': '℗ 2026 Record Label'}),
            'is_explicit': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        }


class AlbumReviewForm(forms.ModelForm):
    class Meta:
        model = AlbumReview
        fields = ('rating', 'title', 'body')
        widgets = {
            'rating': forms.Select(
                choices=[(i, f"{i}/10") for i in range(10, 0, -1)],
                attrs={'class': 'form-select-glass'}
            ),
            'title': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Headline for your review'}),
            'body': forms.Textarea(attrs={'class': 'form-input-glass', 'rows': 5, 'placeholder': 'Write your critical review...'}),
        }
