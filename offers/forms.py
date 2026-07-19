from django import forms
from .models import StudentOffer, OfferRecipient, OfferNote


class StudentOfferForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            perm = 'change_studentoffer' if self.instance and self.instance.pk else 'add_studentoffer'
            branch_ids = [b.pk for b in user.get_branches_for_perm(perm)]
            self.fields['branch'].queryset = self.fields['branch'].queryset.filter(pk__in=branch_ids)
            self.fields['course'].queryset = self.fields['course'].queryset.filter(master__branch__in=branch_ids)

    class Meta:
        model = StudentOffer
        exclude = ['created_by', 'created_at', 'updated_at', 'sent_at', 'master', 'manual_course_name', 'manual_course_hours', 'manual_program_hours']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_description': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class OfferRecipientForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            perm = 'change_studentoffer' if self.instance and self.instance.pk else 'add_studentoffer'
            branch_ids = [b.pk for b in user.get_branches_for_perm(perm)]
            self.fields['offer'].queryset = self.fields['offer'].queryset.filter(branch__in=branch_ids)
            self.fields['student'].queryset = self.fields['student'].queryset.filter(branch__in=branch_ids)

    class Meta:
        model = OfferRecipient
        exclude = ['sent_at', 'opened_at', 'interacted_at']
        widgets = {
            'offer': forms.Select(attrs={'class': 'form-select'}),
            'student': forms.Select(attrs={'class': 'form-select'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class OfferRecipientAddForm(forms.ModelForm):
    """Form to add a recipient directly from an offer detail page (offer is preset)."""
    prospect = forms.ModelChoiceField(queryset=None, required=False, label='المستفسر', widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from prospects.models import Prospect
        if user is not None:
            branch_ids = [b.pk for b in user.get_branches_for_perm('change_studentoffer')]
            self.fields['student'].queryset = self.fields['student'].queryset.filter(branch__in=branch_ids)
            self.fields['prospect'].queryset = Prospect.objects.filter(branch__in=branch_ids).order_by('-created_at')
        else:
            self.fields['prospect'].queryset = Prospect.objects.all().order_by('-created_at')

    class Meta:
        model = OfferRecipient
        exclude = ['offer', 'sent_at', 'opened_at', 'interacted_at']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اسم المستلم'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 966501234567'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        prospect = cleaned_data.get('prospect')
        contact_phone = cleaned_data.get('contact_phone')
        contact_name = cleaned_data.get('contact_name')
        if not student and not prospect and not contact_phone and not contact_name:
            raise forms.ValidationError('يجب اختيار طالب مسجل أو مستفسر أو إدخال بيانات المستلم (اسم + جوال).')
        return cleaned_data


class QuickOfferForm(forms.Form):
    """Form to quickly create an offer + recipient in one step."""
    # Offer fields
    master = forms.ModelChoiceField(queryset=None, label='نوع الاشتراك (التخصص)', widget=forms.Select(attrs={'class': 'form-select'}))
    content = forms.CharField(label=' البيان ووصف العرض ', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    branch = forms.ModelChoiceField(queryset=None, label='الفرع', widget=forms.Select(attrs={'class': 'form-select'}))
    course = forms.ModelChoiceField(queryset=None, required=False, label='الدورة', widget=forms.Select(attrs={'class': 'form-select'}))
    price = forms.DecimalField(max_digits=10, decimal_places=2, initial=0, label='السعر', widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    price_description = forms.CharField(max_length=255, required=False, label='وصف السعر', widget=forms.TextInput(attrs={'class': 'form-control'}))
    # Recipient fields
    contact_name = forms.CharField(max_length=255, label='اسم المشترك', widget=forms.TextInput(attrs={'class': 'form-control'}))
    contact_phone = forms.CharField(max_length=20, label='جوال المشترك', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 966501234567'}))
    contact_email = forms.EmailField(required=False, label='بريد المشترك', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    channel = forms.ChoiceField(choices=OfferRecipient.CHANNEL_CHOICES, initial='whatsapp', label='قناة الإرسال', widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, user=None, **kwargs):
        from core.models import Branch
        from courses.models import Master, Course
        super().__init__(*args, **kwargs)
        if user is not None:
            branch_ids = [b.pk for b in user.get_branches_for_perm('add_studentoffer')]
            self.fields['branch'].queryset = Branch.objects.filter(pk__in=branch_ids)
            self.fields['master'].queryset = Master.objects.select_related('branch').filter(branch__in=branch_ids)
            self.fields['course'].queryset = Course.objects.select_related('master').filter(master__branch__in=branch_ids)
        else:
            self.fields['branch'].queryset = Branch.objects.all()
            self.fields['master'].queryset = Master.objects.select_related('branch').all()
            self.fields['course'].queryset = Course.objects.select_related('master').all()
        # Display course name only in the dropdown
        self.fields['course'].label_from_instance = lambda obj: obj.name or obj.master.name


class RootQuickOfferForm(forms.Form):
    """Form for Root company to create program/course offers quickly."""
    offer_type = forms.ChoiceField(
        choices=[('program', 'بكج / برنامج'), ('course', 'انفرادي / دورة')],
        label='نوع الاشتراك',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    master = forms.ModelChoiceField(queryset=None, required=False, label='التخصص', widget=forms.Select(attrs={'class': 'form-select'}))
    program_hours = forms.IntegerField(required=False, label='عدد ساعات البرنامج', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    course_name = forms.CharField(max_length=255, required=False, label='اسم الدورة', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'اكتب اسم الدورة'}))
    course_hours = forms.IntegerField(required=False, label='عدد ساعات الدورة', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    branch = forms.ModelChoiceField(queryset=None, label='الفرع', widget=forms.Select(attrs={'class': 'form-select'}))
    price = forms.DecimalField(max_digits=10, decimal_places=2, initial=0, label='السعر', widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    price_description = forms.CharField(max_length=255, required=False, label='وصف السعر', widget=forms.TextInput(attrs={'class': 'form-control'}))
    content = forms.CharField(label='البيان ووصف العرض', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    # Prospect selection
    prospect = forms.ModelChoiceField(queryset=None, required=False, label='المستفسر المسجل', widget=forms.Select(attrs={'class': 'form-select'}))
    # New prospect fields
    contact_name = forms.CharField(max_length=255, required=False, label='اسم المستلم', widget=forms.TextInput(attrs={'class': 'form-control'}))
    contact_phone = forms.CharField(max_length=20, required=False, label='جوال المستلم', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'مثال: 966501234567'}))
    contact_email = forms.EmailField(required=False, label='بريد المستلم', widget=forms.EmailInput(attrs={'class': 'form-control'}))
    workplace = forms.CharField(max_length=255, required=False, label='جهة العمل', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ministry = forms.CharField(max_length=255, required=False, label='الوزارة / المؤسسة', widget=forms.TextInput(attrs={'class': 'form-control'}))
    governorate = forms.CharField(max_length=255, required=False, label='المحافظة', widget=forms.TextInput(attrs={'class': 'form-control'}))
    notes = forms.CharField(required=False, label='ملاحظات', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))
    channel = forms.ChoiceField(choices=OfferRecipient.CHANNEL_CHOICES, initial='whatsapp', label='قناة الإرسال', widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, user=None, **kwargs):
        from core.models import Branch
        from courses.models import Master
        from prospects.models import Prospect
        super().__init__(*args, **kwargs)
        if user is not None:
            branch_ids = [b.pk for b in user.get_branches_for_perm('add_studentoffer')]
            self.fields['branch'].queryset = Branch.objects.filter(pk__in=branch_ids)
            self.fields['master'].queryset = Master.objects.select_related('branch').filter(branch__in=branch_ids)
            self.fields['prospect'].queryset = Prospect.objects.filter(branch__in=branch_ids).order_by('-created_at')
        else:
            self.fields['branch'].queryset = Branch.objects.all()
            self.fields['master'].queryset = Master.objects.select_related('branch').all()
            self.fields['prospect'].queryset = Prospect.objects.all().order_by('-created_at')

    def clean(self):
        cleaned_data = super().clean()
        master = cleaned_data.get('master')
        offer_type = cleaned_data.get('offer_type')
        prospect = cleaned_data.get('prospect')
        contact_name = cleaned_data.get('contact_name')
        contact_phone = cleaned_data.get('contact_phone')

        if offer_type == 'program' and not master:
            self.add_error('master', 'يجب اختيار التخصص للبكج / البرنامج.')

        if offer_type == 'program' and master and master.offer_type != 'program':
            self.add_error('master', 'التخصص المختار ليس من نوع بكج / برنامج.')

        if offer_type == 'course' and not cleaned_data.get('course_name'):
            self.add_error('course_name', 'يجب كتابة اسم الدورة.')

        if not prospect and not (contact_name and contact_phone):
            self.add_error('contact_name', 'يجب اختيار مستفسر مسجل أو إدخال اسم وجوال مستفسر جديد.')

        return cleaned_data


class OfferNoteForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            perm = 'change_offernote' if self.instance and self.instance.pk else 'add_offernote'
            branch_ids = [b.pk for b in user.get_branches_for_perm(perm)]
            self.fields['offer'].queryset = self.fields['offer'].queryset.filter(branch__in=branch_ids)

    class Meta:
        model = OfferNote
        exclude = ['person', 'created_at']
        widgets = {
            'offer': forms.Select(attrs={'class': 'form-select'}),
            'note_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
