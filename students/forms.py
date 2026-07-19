from django import forms
from .models import Contact, Student


class StudentForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Branch
        if user is not None:
            if user.is_executive():
                self.fields['branch'].queryset = Branch.objects.all().order_by('code', 'name')
            else:
                allowed = user.get_branches_for_perm('add_student') if not self.instance.pk else user.get_branches_for_perm('change_student')
                self.fields['branch'].queryset = Branch.objects.filter(pk__in=[b.pk for b in allowed]).order_by('code', 'name')
        else:
            self.fields['branch'].queryset = Branch.objects.all().order_by('code', 'name')
        if self.instance and self.instance.pk:
            contact = self.instance.contact
            self.fields['first_name'].initial = contact.first_name
            self.fields['second_name'].initial = contact.second_name
            self.fields['third_name'].initial = contact.third_name
            self.fields['forth_name'].initial = contact.forth_name
            self.fields['address'].initial = contact.address
            self.fields['mobile'].initial = contact.mobile
            self.fields['phone'].initial = contact.phone
            self.fields['nationality'].initial = contact.nationality
            self.fields['identity_number'].initial = contact.identity_number
            self.fields['identity_location'].initial = contact.identity_location
            self.fields['identity_start_date'].initial = contact.identity_start_date
            self.fields['birth_date'].initial = contact.birth_date
            self.fields['birth_location'].initial = contact.birth_location
            self.fields['qualification'].initial = contact.qualification
            self.fields['photo'].initial = contact.photo

    # Contact fields
    first_name = forms.CharField(
        max_length=100, label='الاسم الأول',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    second_name = forms.CharField(
        max_length=100, required=False, label='الاسم الثاني',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    third_name = forms.CharField(
        max_length=100, required=False, label='الاسم الثالث',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    forth_name = forms.CharField(
        max_length=100, label='الاسم الرابع',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        required=False, label='العنوان',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    mobile = forms.CharField(
        max_length=20, required=False, label='المحمول',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        max_length=20, required=False, label='التليفون',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    nationality = forms.CharField(
        max_length=100, required=False, label='الجنسية',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    identity_number = forms.CharField(
        max_length=50, required=False, label='رقم الهوية',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    identity_location = forms.CharField(
        max_length=255, required=False, label='مكان إصدار الهوية',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    identity_start_date = forms.DateField(
        required=False, label='تاريخ إصدار الهوية',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    birth_date = forms.DateField(
        required=False, label='تاريخ الميلاد',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    birth_location = forms.CharField(
        max_length=255, required=False, label='مكان الميلاد',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    qualification = forms.CharField(
        max_length=255, required=False, label='المؤهل',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    photo = forms.ImageField(
        required=False, label='الصورة',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Student
        fields = ['branch', 'level', 'preferred_contact']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'preferred_contact': forms.Select(attrs={'class': 'form-select'}),
        }

