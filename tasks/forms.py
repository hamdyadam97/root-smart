from django import forms
from django.db.models import Q

from accounts.models import Person
from core.models import Branch
from .models import Task, TaskComment, TaskFrequency

FORM_CONTROL = 'form-control'
FORM_SELECT = 'form-select'


def _branches_for(user, perm):
    if user.is_executive():
        return Branch.objects.all()
    return Branch.objects.filter(pk__in=[b.pk for b in user.get_branches_for_perm(perm)])


def _persons_in(branches):
    return Person.objects.filter(
        Q(branch__in=branches) | Q(employee_roles__branch__in=branches), is_active=True,
    ).distinct().order_by('first_name', 'forth_name')


class TaskForm(forms.ModelForm):
    assignees = forms.ModelMultipleChoiceField(
        queryset=Person.objects.none(), widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='الموظفون المكلفون',
    )

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'branch', 'priority', 'mode', 'frequency',
            'start_date', 'due_date', 'weekly_comment_count',
            'late_penalty_amount', 'missed_comment_penalty_amount',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': FORM_CONTROL}),
            'description': forms.Textarea(attrs={'class': FORM_CONTROL, 'rows': 4}),
            'branch': forms.Select(attrs={'class': FORM_SELECT}),
            'priority': forms.Select(attrs={'class': FORM_SELECT}),
            'mode': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'frequency': forms.Select(attrs={'class': FORM_SELECT}),
            'start_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}, format='%Y-%m-%d'),
            'due_date': forms.DateInput(attrs={'class': FORM_CONTROL, 'type': 'date'}, format='%Y-%m-%d'),
            'weekly_comment_count': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 1, 'max': 7}),
            'late_penalty_amount': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
            'missed_comment_penalty_amount': forms.NumberInput(attrs={'class': FORM_CONTROL, 'min': 0, 'step': '0.01'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        perm = 'change_task' if self.instance.pk else 'add_task'
        branches = _branches_for(user, perm)
        if self.instance.pk:
            branches = branches | Branch.objects.filter(pk=self.instance.branch_id)
        self.fields['branch'].queryset = branches.distinct()
        self.fields['assignees'].queryset = _persons_in(branches)
        if self.instance.pk:
            self.initial['assignees'] = list(self.instance.assignees.values_list('pk', flat=True))

    def clean_late_penalty_amount(self):
        value = self.cleaned_data['late_penalty_amount']
        if value is not None and value < 0:
            raise forms.ValidationError('المبلغ لا يمكن أن يكون سالبًا.')
        return value

    def clean_missed_comment_penalty_amount(self):
        value = self.cleaned_data['missed_comment_penalty_amount']
        if value is not None and value < 0:
            raise forms.ValidationError('المبلغ لا يمكن أن يكون سالبًا.')
        return value

    def clean(self):
        cleaned = super().clean()
        branch = cleaned.get('branch')
        assignees = cleaned.get('assignees')
        if branch and assignees:
            allowed = set(_persons_in([branch]).values_list('pk', flat=True))
            outside = [p for p in assignees if p.pk not in allowed]
            if outside:
                names = '، '.join(' '.join(p.get_full_name().split()) for p in outside)
                self.add_error('assignees', f'هؤلاء الموظفون ليسوا من الفرع المختار: {names}')
        if cleaned.get('frequency') != TaskFrequency.WEEKLY:
            cleaned['weekly_comment_count'] = cleaned.get('weekly_comment_count') or 1
        return cleaned


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['body', 'attachment']
        widgets = {
            'body': forms.Textarea(attrs={'class': FORM_CONTROL, 'rows': 3, 'placeholder': 'اكتب تحديثك على المهمة...'}),
            'attachment': forms.ClearableFileInput(attrs={'class': FORM_CONTROL}),
        }
