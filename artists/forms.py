"""
Forms for Artist Profile, Verification Requests, and Payout Configuration.
"""
from django import forms
from .models import Artist, ArtistVerificationRequest, PayoutAccount, ArtistMember


class ArtistProfileForm(forms.ModelForm):
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-file-glass', 'accept': 'image/*'})
    )
    header_banner = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-file-glass', 'accept': 'image/*'})
    )

    class Meta:
        model = Artist
        fields = (
            'name',
            'stage_name',
            'bio',
            'genres',
            'country_of_origin',
            'avatar',
            'header_banner',
            'website',
            'spotify_id',
            'soundcloud_id',
            'youtube_channel',
            'instagram_handle',
            'twitter_handle',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Artist / Band Name'}),
            'stage_name': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Stage Name'}),
            'bio': forms.Textarea(attrs={'class': 'form-input-glass', 'rows': 5, 'placeholder': 'Artist biography and musical trajectory...'}),
            'genres': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'e.g. Synthwave, Electronic, Ambient'}),
            'country_of_origin': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'e.g. United Kingdom'}),
            'website': forms.URLInput(attrs={'class': 'form-input-glass', 'placeholder': 'https://artistwebsite.com'}),
            'spotify_id': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Spotify Artist URI/ID'}),
            'soundcloud_id': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'SoundCloud profile handle'}),
            'youtube_channel': forms.URLInput(attrs={'class': 'form-input-glass', 'placeholder': 'https://youtube.com/@channel'}),
            'instagram_handle': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': '@instagram_username'}),
            'twitter_handle': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': '@twitter_username'}),
        }


class ArtistVerificationRequestForm(forms.ModelForm):
    official_id_document = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={'class': 'form-file-glass', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )

    class Meta:
        model = ArtistVerificationRequest
        fields = ('legal_name', 'official_id_document', 'social_proof_links', 'notes')
        widgets = {
            'legal_name': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Legal Full Name or Entity'}),
            'social_proof_links': forms.Textarea(attrs={'class': 'form-input-glass', 'rows': 4, 'placeholder': 'Provide Spotify For Artists, Apple Music, Twitter/Instagram links'}),
            'notes': forms.Textarea(attrs={'class': 'form-input-glass', 'rows': 3, 'placeholder': 'Optional additional information for moderators'}),
        }


class PayoutAccountForm(forms.ModelForm):
    class Meta:
        model = PayoutAccount
        fields = ('account_type', 'beneficiary_name', 'account_identifier', 'currency')
        widgets = {
            'account_type': forms.Select(attrs={'class': 'form-select-glass'}),
            'beneficiary_name': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Account Holder Legal Name'}),
            'account_identifier': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Stripe Connect ID, PayPal Email, or IBAN'}),
            'currency': forms.Select(
                choices=[('USD', 'USD ($)'), ('EUR', 'EUR (€)'), ('GBP', 'GBP (£)')],
                attrs={'class': 'form-select-glass'}
            ),
        }
