from django import forms
from students.models import Student
from .models import Account, AttachType, Attach, AccountAttach, AccountCondition, AccountNote


class AccountForm(forms.ModelForm):
    prospect = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='المستفسر',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from courses.models import Course
        from prospects.models import Prospect
        from prospects.utils import get_user_root_branch_ids
        self.fields['student'].required = False
        perm = 'change_registration' if self.instance and self.instance.pk else 'add_registration'
        if user is not None:
            if user.is_executive():
                self.fields['course'].queryset = Course.objects.all().order_by('-created_at')
                self.fields['student'].queryset = Student.objects.all().order_by('-created_at')
                self.fields['prospect'].queryset = Prospect.objects.filter(student__isnull=True).order_by('-created_at')
            else:
                allowed = user.get_branches_for_perm(perm)
                allowed_ids = [b.pk for b in allowed]
                self.fields['course'].queryset = Course.objects.filter(
                    master__branch_id__in=allowed_ids
                ).order_by('-created_at')
                self.fields['student'].queryset = Student.objects.filter(
                    branch_id__in=allowed_ids
                ).order_by('-created_at')
                root_ids = get_user_root_branch_ids(user, perm)
                self.fields['prospect'].queryset = Prospect.objects.filter(
                    student__isnull=True, branch_id__in=root_ids
                ).order_by('-created_at')
        else:
            self.fields['prospect'].queryset = Prospect.objects.filter(student__isnull=True).order_by('-created_at')

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        student = cleaned_data.get('student')
        prospect = cleaned_data.get('prospect')

        # في شركة الجذور، المستفسر بديل عن الطالب
        if course and course.master and course.master.branch and self._is_root_branch(course.master.branch):
            if not prospect and not student:
                self.add_error('prospect', 'يرجى اختيار مستفسر')
        else:
            if not student:
                self.add_error('student', 'يرجى اختيار طالب')

        return cleaned_data

    def _is_root_branch(self, branch):
        from prospects.utils import is_root_branch
        return is_root_branch(branch)

    class Meta:
        model = Account
        fields = [
            'course', 'student', 'prospect', 'code', 'register_date',
            'course_payment_type', 'course_price', 'course_discount_amount',
            'course_profit_amount', 'course_credit_amount', 'note',
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'student': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'register_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'course_payment_type': forms.Select(attrs={'class': 'form-select'}),
            'course_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'course_discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'course_profit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'course_credit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AttachTypeForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = AttachType
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AttachForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Attach
        fields = ['attach_type', 'title', 'file_data', 'file_name', 'file_type']
        widgets = {
            'attach_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'file_data': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'file_name': forms.TextInput(attrs={'class': 'form-control'}),
            'file_type': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AccountAttachForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        perm = 'change_accountattach' if self.instance and self.instance.pk else 'add_accountattach'
        if user is not None:
            if user.is_executive():
                self.fields['account'].queryset = Account.objects.all().order_by('-created_at')
                self.fields['attach'].queryset = Attach.objects.all().order_by('-created_at')
            else:
                allowed = user.get_branches_for_perm(perm)
                allowed_ids = [b.pk for b in allowed]
                self.fields['account'].queryset = Account.objects.filter(
                    course__master__branch_id__in=allowed_ids
                ).order_by('-created_at')
                self.fields['attach'].queryset = Attach.objects.filter(
                    person__branch_id__in=allowed_ids
                ).order_by('-created_at')

    class Meta:
        model = AccountAttach
        fields = ['account', 'attach']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'attach': forms.Select(attrs={'class': 'form-select'}),
        }


class AccountConditionForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        perm = 'change_accountcondition' if self.instance and self.instance.pk else 'add_accountcondition'
        if user is not None:
            if user.is_executive():
                self.fields['account'].queryset = Account.objects.all().order_by('-created_at')
            else:
                allowed = user.get_branches_for_perm(perm)
                allowed_ids = [b.pk for b in allowed]
                self.fields['account'].queryset = Account.objects.filter(
                    course__master__branch_id__in=allowed_ids
                ).order_by('-created_at')

    class Meta:
        model = AccountCondition
        fields = ['account', 'title', 'content', 'fulfilled']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fulfilled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AccountNoteForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        perm = 'change_accountnote' if self.instance and self.instance.pk else 'add_accountnote'
        if user is not None:
            if user.is_executive():
                self.fields['account'].queryset = Account.objects.all().order_by('-created_at')
            else:
                allowed = user.get_branches_for_perm(perm)
                allowed_ids = [b.pk for b in allowed]
                self.fields['account'].queryset = Account.objects.filter(
                    course__master__branch_id__in=allowed_ids
                ).order_by('-created_at')

    class Meta:
        model = AccountNote
        fields = ['account', 'content']
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
