from django import forms
from core.models import Branch
from courses.models import Master, Course
from .models import Prospect, ProspectOffer
from .utils import get_root_branch_queryset


class ProspectForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # مقتصر على فروع شركة الجذور الرقمية
        branch_qs = get_root_branch_queryset().order_by('code', 'name')
        if user is not None and not user.is_executive():
            perm = 'add_prospect' if not self.instance.pk else 'change_prospect'
            allowed = user.get_branches_for_perm(perm)
            branch_qs = branch_qs.filter(pk__in=[b.pk for b in allowed])

        self.fields['branch'].queryset = branch_qs
        self.fields['master'].queryset = Master.objects.select_related('branch').filter(branch__in=branch_qs).order_by('-created_at')

        # تخصيص الحقول
        self.fields['contact_date'].widget.attrs.update({'type': 'date'})

    class Meta:
        model = Prospect
        fields = [
            'branch', 'name', 'mobile', 'master',
            'workplace', 'ministry', 'governorate',
            'communication_method', 'notes', 'contact_date',
            'contacted_by', 'status',
        ]
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'master': forms.Select(attrs={'class': 'form-select'}),
            'workplace': forms.TextInput(attrs={'class': 'form-control'}),
            'ministry': forms.TextInput(attrs={'class': 'form-control'}),
            'governorate': forms.TextInput(attrs={'class': 'form-control'}),
            'communication_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_date': forms.DateInput(attrs={'class': 'form-control'}),
            'contacted_by': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class ProspectOfferForm(forms.ModelForm):
    def __init__(self, *args, prospect=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.prospect = prospect
        self.user = user
        if prospect:
            self.fields['prospect'].initial = prospect
            self.fields['branch'].initial = prospect.branch
            self.fields['branch'].queryset = Branch.objects.filter(pk=prospect.branch_id)
            self.fields['course'].queryset = Course.objects.select_related('master').filter(master__branch=prospect.branch).order_by('-created_at')
        elif user is not None:
            if user.is_executive():
                self.fields['branch'].queryset = Branch.objects.all().order_by('code', 'name')
            else:
                allowed = user.get_branches_for_perm('add_prospectoffer')
                self.fields['branch'].queryset = Branch.objects.filter(pk__in=[b.pk for b in allowed]).order_by('code', 'name')

    class Meta:
        model = ProspectOffer
        fields = ['prospect', 'branch', 'title', 'course', 'content', 'price', 'sent_by', 'sent_at', 'status']
        widgets = {
            'prospect': forms.HiddenInput(),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sent_by': forms.Select(attrs={'class': 'form-select'}),
            'sent_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
