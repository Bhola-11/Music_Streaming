"""
Forms for Playlist Creation, Metadata Editing, Collaborator Management, and Track Assignment.
"""
from django import forms
from django.contrib.auth import get_user_model
from .models import Playlist, PlaylistTrack, PlaylistCollaborator, CollaboratorRole

User = get_user_model()


class PlaylistForm(forms.ModelForm):
    cover_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-file-glass', 'accept': 'image/*'})
    )

    class Meta:
        model = Playlist
        fields = ('title', 'description', 'privacy', 'is_collaborative', 'cover_image')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Playlist Title'}),
            'description': forms.Textarea(attrs={'class': 'form-input-glass', 'rows': 4, 'placeholder': 'Describe the vibe, moods, or theme...'}),
            'privacy': forms.Select(attrs={'class': 'form-select-glass'}),
            'is_collaborative': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        }


class AddCollaboratorForm(forms.Form):
    username_or_email = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Friend username or email'})
    )
    role = forms.ChoiceField(
        choices=CollaboratorRole.choices,
        widget=forms.Select(attrs={'class': 'form-select-glass'})
    )

    def clean_username_or_email(self):
        query = self.cleaned_data['username_or_email'].strip()
        user = User.objects.filter(email__iexact=query).first() or User.objects.filter(username__iexact=query).first()
        if not user:
            raise forms.ValidationError("No user found with that username or email.")
        return user
