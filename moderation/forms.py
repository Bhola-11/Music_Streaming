"""
Forms for Submitting Content Violation Reports and DMCA Takedown Notices.
"""
from django import forms
from .models import ModerationReport, TakedownRequest, ReportReason


class FileReportForm(forms.ModelForm):
    class Meta:
        model = ModerationReport
        fields = ('reason', 'description', 'evidence_url')
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-select-glass'}),
            'description': forms.Textarea(attrs={'class': 'form-input-glass', 'rows': 5, 'placeholder': 'Provide specific details regarding the infringement or violation...'}),
            'evidence_url': forms.URLInput(attrs={'class': 'form-input-glass', 'placeholder': 'Optional link to copyright registration or original source'}),
        }


class SubmitDMCAForm(forms.ModelForm):
    class Meta:
        model = TakedownRequest
        fields = ('claimant_name', 'claimant_email', 'copyright_owner', 'work_title', 'statement_of_authority')
        widgets = {
            'claimant_name': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Your Legal Full Name'}),
            'claimant_email': forms.EmailInput(attrs={'class': 'form-input-glass', 'placeholder': 'Official contact email'}),
            'copyright_owner': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Copyright Holder / Label Name'}),
            'work_title': forms.TextInput(attrs={'class': 'form-input-glass', 'placeholder': 'Title of Original Work'}),
            'statement_of_authority': forms.CheckboxInput(attrs={'class': 'form-checkbox-glass'}),
        }
