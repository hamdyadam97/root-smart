from django import forms
from .models import Payment, PaymentOut, Deposit, Withdraw, BillBuyType, BillBuy, Offer, Call


class PaymentForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from registrations.models import Account
        queryset = Account.objects.select_related('student', 'course', 'course__master')
        if user is not None:
            if user.is_executive():
                self.fields['account'].queryset = queryset.all()
            else:
                perm = 'add_payment' if not self.instance.pk else 'change_payment'
                allowed = [b.pk for b in user.get_branches_for_perm(perm)]
                self.fields['account'].queryset = queryset.filter(course__master__branch__pk__in=allowed)
        else:
            self.fields['account'].queryset = queryset.all()

    class Meta:
        model = Payment
        fields = [
            'account', 'code', 'date', 'amount_number', 'amount_string',
            'type', 'payment_method', 'payment_method_code', 'note',
        ]
        widgets = {
            'account': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'amount_number': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount_string': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'payment_method_code': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PaymentOutForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = PaymentOut
        fields = [
            'code', 'date', 'amount_number', 'amount_string',
            'receiver_name', 'reason', 'payment_method',
        ]
        widgets = {
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'amount_number': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'amount_string': forms.TextInput(attrs={'class': 'form-control'}),
            'receiver_name': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
        }


class DepositForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Bank
        queryset = Bank.objects.select_related('branch')
        if user is not None:
            if user.is_executive():
                self.fields['bank'].queryset = queryset.all()
            else:
                perm = 'add_deposit' if not self.instance.pk else 'change_deposit'
                allowed = [b.pk for b in user.get_branches_for_perm(perm)]
                self.fields['bank'].queryset = queryset.filter(branch__pk__in=allowed)
        else:
            self.fields['bank'].queryset = queryset.all()

    class Meta:
        model = Deposit
        fields = ['code', 'date', 'amount', 'bank', 'note']
        widgets = {
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bank': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class WithdrawForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Bank
        queryset = Bank.objects.select_related('branch')
        if user is not None:
            if user.is_executive():
                self.fields['bank'].queryset = queryset.all()
            else:
                perm = 'add_withdraw' if not self.instance.pk else 'change_withdraw'
                allowed = [b.pk for b in user.get_branches_for_perm(perm)]
                self.fields['bank'].queryset = queryset.filter(branch__pk__in=allowed)
        else:
            self.fields['bank'].queryset = queryset.all()

    class Meta:
        model = Withdraw
        fields = ['code', 'date', 'amount', 'bank', 'note']
        widgets = {
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bank': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BillBuyTypeForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = BillBuyType
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BillBuyForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = BillBuy
        fields = [
            'code', 'date', 'bill_buy_type', 'supplier',
            'amount', 'tax', 'discount', 'note',
        ]
        widgets = {
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'bill_buy_type': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class OfferForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        from courses.models import Master
        queryset = Master.objects.select_related('branch')
        if user is not None:
            if user.is_executive():
                self.fields['master'].queryset = queryset.all()
            else:
                perm = 'add_offer_price' if not self.instance.pk else 'change_offer_price'
                allowed = [b.pk for b in user.get_branches_for_perm(perm)]
                self.fields['master'].queryset = queryset.filter(branch__pk__in=allowed)
        else:
            self.fields['master'].queryset = queryset.all()

    class Meta:
        model = Offer
        fields = [
            'master', 'code', 'customer_name', 'customer_identity_number',
            'customer_mobile', 'customer_email', 'note', 'message_body',
            'master_payment_type', 'master_price', 'master_discount_amount',
            'master_profit_amount', 'master_credit_amount',
            'send_email', 'send_sms', 'sms_body', 'registered',
        ]
        widgets = {
            'master': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.NumberInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_identity_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'message_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'master_payment_type': forms.Select(attrs={'class': 'form-select'}),
            'master_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'master_discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'master_profit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'master_credit_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'send_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sms_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'registered': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CallForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Offer.objects.select_related('master')
        if user is not None:
            if user.is_executive():
                self.fields['offer'].queryset = queryset.all()
            else:
                perm = 'add_call' if not self.instance.pk else 'change_call'
                allowed = [b.pk for b in user.get_branches_for_perm(perm)]
                self.fields['offer'].queryset = queryset.filter(master__branch__pk__in=allowed)
        else:
            self.fields['offer'].queryset = queryset.all()

    class Meta:
        model = Call
        fields = ['offer', 'call_type', 'duration', 'notes']
        widgets = {
            'offer': forms.Select(attrs={'class': 'form-select'}),
            'call_type': forms.Select(attrs={'class': 'form-select'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
