from django import forms
from .models import ReportSnapshot


class ReportSnapshotForm(forms.ModelForm):
    class Meta:
        model = ReportSnapshot
        exclude = ['generated_by', 'created_at', 'data_json']
        widgets = {
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'period': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
