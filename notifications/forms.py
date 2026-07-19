from django import forms
from .models import AppNotification


class AppNotificationForm(forms.ModelForm):
    class Meta:
        model = AppNotification
        exclude = ['user', 'created_at', 'is_read']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'action_url': forms.TextInput(attrs={'class': 'form-control'}),
        }
