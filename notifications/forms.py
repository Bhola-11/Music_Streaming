"""
Forms for User Notification Preferences.
"""
from django import forms
from .models import NotificationPreference


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = (
            'notify_new_releases',
            'notify_playlist_collaborations',
            'notify_social_followers',
            'notify_royalty_earnings',
            'notify_security_events',
            'email_digests',
        )
        widgets = {
            'notify_new_releases': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'notify_playlist_collaborations': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'notify_social_followers': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'notify_royalty_earnings': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'notify_security_events': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
            'email_digests': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        }
