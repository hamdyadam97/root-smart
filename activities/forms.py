from decimal import Decimal

from django import forms

from core.models import Branch
from .models import Activity, FinancialAnalysis, ActivityCoordination, FinalFinancialAnalysis

FORM_CONTROL = 'form-control'
FORM_SELECT = 'form-select'
FORM_CHECK = 'form-check-input'


def _accessible_branches(user):
    if user.is_executive():
        return Branch.objects.all()
    return Branch.objects.filter(pk__in=[b.pk for b in user.get_accessible_branches()])


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = [
            'branch', 'request_number', 'form_number', 'form_date',
            'name', 'location', 'event_date', 'activity_type', 'target_audience',
            'region', 'accreditation_type', 'expected_attendees', 'trainer_name',
            'no_partner', 'partner_kind', 'partner_name', 'partner_share_percent',
            'authorized_signatory', 'coordinator_name',
        ]
        widgets = {
            'branch': forms.Select(attrs={'class': FORM_SELECT}),
            'request_number': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 1}),
            'form_number': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 1}),
            'form_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}),
            'name': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'location': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'event_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}),
            'activity_type': forms.Select(attrs={'class': FORM_SELECT}),
            'target_audience': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'region': forms.Select(attrs={'class': FORM_SELECT}),
            'accreditation_type': forms.Select(attrs={'class': FORM_SELECT}),
            'expected_attendees': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0}),
            'trainer_name': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'no_partner': forms.CheckboxInput(attrs={'class': FORM_CHECK}),
            'partner_kind': forms.Select(attrs={'class': FORM_SELECT}),
            'partner_name': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'partner_share_percent': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'max': 100, 'step': '0.01'}),
            'authorized_signatory': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'coordinator_name': forms.TextInput(attrs={'class': FORM_CONTROL}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['branch'].queryset = _accessible_branches(user)
        # رقم الطلب ورقم النموذج يُرقمان تلقائيًا ولا يُدخلهما المستخدم
        self.fields['request_number'].disabled = True
        self.fields['form_number'].disabled = True
        # حقول الشريك تُقيَّم في clean() وفق خيار "لا يوجد شريك"
        self.fields['partner_kind'].required = False
        self.fields['partner_name'].required = False
        self.fields['partner_share_percent'].required = False

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('no_partner'):
            cleaned['partner_kind'] = ''
            cleaned['partner_name'] = ''
            cleaned['partner_share_percent'] = Decimal('0.00')
        elif not cleaned.get('partner_share_percent'):
            self.add_error('partner_share_percent', 'أدخل نسبة الشريك أو المنسق من صافي الأرباح.')
        return cleaned


class FinancialAnalysisForm(forms.ModelForm):
    class Meta:
        model = FinancialAnalysis
        fields = [
            'form_number', 'analysis_date',
            'trainee_count', 'fee_per_trainee', 'actual_trainee_fees',
            'expected_electricity', 'actual_electricity',
            'expected_water', 'actual_water',
            'expected_hall', 'actual_hall',
            'expected_hospitality', 'actual_hospitality',
            'expected_certificates', 'actual_certificates',
            'expected_trainer_fee', 'actual_trainer_fee',
            'prepared_by', 'preparer_job_title', 'preparer_signature_date',
            'approval_name', 'approval_date',
        ]
        widgets = {
            'form_number': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 1}),
            'analysis_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}),
            'trainee_count': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0}),
            'fee_per_trainee': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_trainee_fees': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'expected_electricity': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_electricity': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'expected_water': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_water': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'expected_hall': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_hall': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'expected_hospitality': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_hospitality': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'expected_certificates': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_certificates': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'expected_trainer_fee': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_trainer_fee': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'prepared_by': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'preparer_job_title': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'preparer_signature_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}),
            'approval_name': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'approval_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.form_number:
            self.fields['form_number'].disabled = True
        if not self.instance.pk and self.instance.activity_id:
            self.initial.setdefault('trainee_count', self.instance.activity.expected_attendees)
        # معد التحليل هو المستخدم الحالي — يظهر اسمه تلقائيًا ولا يُعدَّل
        if user is not None:
            self.initial.setdefault('prepared_by', user.get_full_name() or user.email)
        self.fields['prepared_by'].widget.attrs['readonly'] = True


class FinalFinancialAnalysisForm(forms.ModelForm):
    class Meta:
        model = FinalFinancialAnalysis
        fields = [
            'form_number', 'analysis_date',
            'trainee_count', 'fee_per_trainee',
            'actual_electricity', 'actual_water', 'actual_hall',
            'actual_hospitality', 'actual_certificates', 'actual_trainer_fee',
            'prepared_by', 'approval_name', 'approval_date',
        ]
        widgets = {
            'form_number': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 1}),
            'analysis_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}),
            'trainee_count': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0}),
            'fee_per_trainee': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_electricity': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_water': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_hall': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_hospitality': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_certificates': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'actual_trainer_fee': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'prepared_by': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'approval_name': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'approval_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.form_number:
            self.fields['form_number'].disabled = True
        if not self.instance.pk and self.instance.activity_id:
            coordination = ActivityCoordination.objects.filter(activity=self.instance.activity).first()
            self.initial.setdefault('trainee_count', coordination.attended_count if coordination else self.instance.activity.expected_attendees)
        # معد التحليل هو المستخدم الحالي — يظهر اسمه تلقائيًا ولا يُعدَّل
        if user is not None:
            self.initial.setdefault('prepared_by', user.get_full_name() or user.email)
        self.fields['prepared_by'].widget.attrs['readonly'] = True


class ActivityCoordinationForm(forms.ModelForm):
    class Meta:
        model = ActivityCoordination
        fields = [
            'form_number', 'coordination_date',
            'lecturer_name', 'lecturer_phone', 'expected_attendees',
            'hospitality_included', 'coordinator_name',
            'start_time', 'end_time',
            'registered_count', 'attended_count',
            'signed_name', 'signature_date',
        ]
        widgets = {
            'form_number': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 1}),
            'coordination_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}),
            'lecturer_name': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'lecturer_phone': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'expected_attendees': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0}),
            'hospitality_included': forms.CheckboxInput(attrs={'class': FORM_CHECK}),
            'coordinator_name': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'start_time': forms.TimeInput(attrs={'class': FORM_CONTROL, 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': FORM_CONTROL, 'type': 'time'}),
            'registered_count': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0}),
            'attended_count': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0}),
            'signed_name': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'signature_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.form_number:
            self.fields['form_number'].disabled = True
        self.fields['expected_attendees'].required = False
        if not self.instance.pk and self.instance.activity_id:
            self.initial.setdefault('expected_attendees', self.instance.activity.expected_attendees)
            self.initial.setdefault('coordinator_name', self.instance.activity.coordinator_name)
