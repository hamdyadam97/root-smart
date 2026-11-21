from django import forms
from django.forms import inlineformset_factory

from .models import DisbursementRequest, DisbursementDetail


class DisbursementRequestForm(forms.ModelForm):
    SUPERVISOR_FIELDS = ('supervisor_name', 'supervisor_signed_name', 'supervisor_signature_date')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        can_approve = False
        if user is not None and user.is_authenticated:
            if self.instance.pk:
                can_approve = self.instance.can_user_approve(user)
            else:
                can_approve = user.is_executive() or user.has_perm_on_any_branch(self.instance.approve_perm)
        if not can_approve:
            for name in self.SUPERVISOR_FIELDS:
                self.fields[name].widget.attrs['readonly'] = 'readonly'

    class Meta:
        model = DisbursementRequest
        fields = [
            'entity_name', 'subject', 'date',
            'amount_number', 'amount_string', 'reason', 'payment_method', 'purpose',
            'requester_name', 'requester_job_title', 'requester_signed_name',
            'supervisor_name', 'supervisor_signed_name', 'supervisor_signature_date',
            'disbursed_date', 'disbursed_by_name', 'disbursed_signed_name',
            'notes',
        ]
        widgets = {
            'entity_name': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'amount_number': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount_string': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'requester_name': forms.TextInput(attrs={'class': 'form-control'}),
            'requester_job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'requester_signed_name': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisor_signed_name': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisor_signature_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'disbursed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'disbursed_by_name': forms.TextInput(attrs={'class': 'form-control'}),
            'disbursed_signed_name': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DisbursementDetailForm(forms.ModelForm):
    class Meta:
        model = DisbursementDetail
        fields = ['description', 'amount']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'البيان'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control detail-amount', 'step': '0.01', 'placeholder': '0.00'}),
        }


DisbursementDetailFormSet = inlineformset_factory(
    DisbursementRequest, DisbursementDetail,
    form=DisbursementDetailForm,
    extra=1, can_delete=True, min_num=0,
)
