from django import forms
from .models import InternalMessage


class InternalMessageForm(forms.ModelForm):
    class Meta:
        model = InternalMessage
        exclude = ['sender', 'created_at', 'is_read']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'message_type': forms.Select(attrs={'class': 'form-select'}),
        }
