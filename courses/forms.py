from django import forms
from django.db.models import Q

from accounts.mixins import filter_by_branch

from .models import Master, Course


class MasterForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            perm = 'add_master' if self.instance.pk is None else 'change_master'
            allowed_branches = user.get_branches_for_perm(perm)
            allowed_ids = [b.pk for b in allowed_branches]
            self.fields['branch'].queryset = self.fields['branch'].queryset.filter(
                pk__in=allowed_ids
            )
            self.fields['master_category'].queryset = self.fields['master_category'].queryset.filter(
                Q(branch__in=allowed_ids) | Q(branch__isnull=True)
            )

    class Meta:
        model = Master
        fields = ['branch', 'master_category', 'code', 'name', 'period', 'hours', 'offer_type']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'master_category': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'يتم التوليد تلقائيًا إذا تركته فارغًا'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'period': forms.TextInput(attrs={'class': 'form-control'}),
            'hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'offer_type': forms.Select(attrs={'class': 'form-select'}),
        }


class CourseForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            perm = 'add_course' if self.instance.pk is None else 'change_course'
            self.fields['master'].queryset = filter_by_branch(
                self.fields['master'].queryset,
                user,
                'branch',
                perm=perm,
            )

    class Meta:
        model = Course
        fields = ['master', 'code', 'name', 'instructor', 'company_name', 'max_student_count', 'target_level', 'hours', 'start_date', 'end_date']
        widgets = {
            'master': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'يتم التوليد تلقائيًا إذا تركته فارغًا'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'instructor': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'max_student_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'target_level': forms.Select(attrs={'class': 'form-select'}),
            'hours': forms.NumberInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
