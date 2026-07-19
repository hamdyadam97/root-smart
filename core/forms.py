from django import forms
from .models import Company, Branch, Bank, MasterCategory


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 'sub_name', 'currency', 'address', 'phone1', 'phone2',
            'postal_code', 'mobile', 'fax', 'email', 'website',
            'commercial_registration', 'tax_code', 'logo'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_name': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone1': forms.TextInput(attrs={'class': 'form-control'}),
            'phone2': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'commercial_registration': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_code': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = [
            'company', 'code', 'name', 'sub_name', 'address',
            'phone1', 'phone2', 'postal_code', 'mobile', 'fax',
            'email', 'website', 'commercial_registration',
            'licence_code', 'tax_code', 'logo', 'signature'
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'phone1': forms.TextInput(attrs={'class': 'form-control'}),
            'phone2': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'commercial_registration': forms.TextInput(attrs={'class': 'form-control'}),
            'licence_code': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_code': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'signature': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class BankForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Branch
        if user is not None:
            if user.is_executive():
                self.fields['branch'].queryset = Branch.objects.all().order_by('code', 'name')
            else:
                perm = 'add_bank' if not self.instance.pk else 'change_bank'
                allowed = user.get_branches_for_perm(perm)
                self.fields['branch'].queryset = Branch.objects.filter(pk__in=[b.pk for b in allowed]).order_by('code', 'name')
        else:
            self.fields['branch'].queryset = Branch.objects.all().order_by('code', 'name')

    class Meta:
        model = Bank
        fields = ['branch', 'name', 'account_number', 'iban', 'swift']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_number': forms.TextInput(attrs={'class': 'form-control'}),
            'iban': forms.TextInput(attrs={'class': 'form-control'}),
            'swift': forms.TextInput(attrs={'class': 'form-control'}),
        }


class MasterCategoryForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Branch
        if user is not None:
            if user.is_executive():
                self.fields['branch'].queryset = Branch.objects.all().order_by('code', 'name')
            else:
                perm = 'add_mastercategory' if not self.instance.pk else 'change_mastercategory'
                allowed = user.get_branches_for_perm(perm)
                self.fields['branch'].queryset = Branch.objects.filter(pk__in=[b.pk for b in allowed]).order_by('code', 'name')
        else:
            self.fields['branch'].queryset = Branch.objects.all().order_by('code', 'name')

    class Meta:
        model = MasterCategory
        fields = ['branch', 'name']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
