from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone

from registrations.models import Account
from accounts.mixins import BranchPermissionMixin, ProtectedDeleteMixin, filter_by_branch
from .models import (
    Payment, PaymentOut, Deposit, Withdraw, BillBuyType, BillBuy, Offer, Call,
    DisbursementRequest, DisbursementStatus,
)
from .forms import (
    PaymentForm, PaymentOutForm, DepositForm, WithdrawForm,
    BillBuyTypeForm, BillBuyForm, OfferForm, CallForm,
    DisbursementRequestForm, DisbursementDetailFormSet,
)


# ============================================================
# Payment Views
# ============================================================

class PaymentListView(BranchPermissionMixin, ListView):
    model = Payment
    template_name = 'finance/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 20
    required_perm = 'view_payment'
    branch_field = 'account__course__master__branch'

    def get_queryset(self):
        queryset = Payment.objects.select_related('account', 'last_person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(code__icontains=search)
        account = self.request.GET.get('account')
        if account:
            queryset = queryset.filter(account_id=account)
        payment_type = self.request.GET.get('type')
        if payment_type:
            queryset = queryset.filter(type=payment_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accounts'] = Account.objects.select_related('student', 'course', 'course__master').all()
        return context


class PaymentDetailView(BranchPermissionMixin, DetailView):
    model = Payment
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'finance/payment_detail.html'
    context_object_name = 'payment'
    required_perm = 'view_payment'
    branch_field = 'account__course__master__branch'

    def get_queryset(self):
        return Payment.objects.select_related('account', 'last_person')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['accounts'] = Account.objects.select_related('student', 'course', 'course__master').all()
        return context


class PaymentCreateView(BranchPermissionMixin, CreateView):
    model = Payment
    form_class = PaymentForm
    template_name = 'finance/payment_form.html'
    success_url = reverse_lazy('payment-list')
    required_perm = 'add_payment'
    branch_field = 'account__course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class PaymentUpdateView(BranchPermissionMixin, UpdateView):
    model = Payment
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = PaymentForm
    template_name = 'finance/payment_form.html'
    success_url = reverse_lazy('payment-list')
    required_perm = 'change_payment'
    branch_field = 'account__course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class PaymentDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = Payment
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'finance/payment_confirm_delete.html'
    success_url = reverse_lazy('payment-list')
    required_perm = 'delete_payment'
    branch_field = 'account__course__master__branch'


@require_POST
def payment_create_ajax(request):
    if not request.user.has_perm_on_any_branch('add_payment'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = PaymentForm(request.POST, user=request.user)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.last_person = request.user
        payment.save()
        return JsonResponse({'success': True, 'message': 'تم إنشاء السند بنجاح', 'id': payment.id, 'slug': payment.slug})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_POST
def payment_update_ajax(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if not request.user.has_perm('change_payment', branch=payment.account.course.master.branch):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = PaymentForm(request.POST, instance=payment, user=request.user)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.last_person = request.user
        payment.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث السند بنجاح'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ============================================================
# PaymentOut Views
# ============================================================

class PaymentOutListView(BranchPermissionMixin, ListView):
    model = PaymentOut
    template_name = 'finance/paymentout_list.html'
    context_object_name = 'payment_outs'
    paginate_by = 20
    required_perm = 'view_paymentout'
    branch_field = 'last_person__branch'


class PaymentOutDetailView(BranchPermissionMixin, DetailView):
    model = PaymentOut
    template_name = 'finance/paymentout_detail.html'
    context_object_name = 'payment_out'
    required_perm = 'view_paymentout'
    branch_field = 'last_person__branch'


class PaymentOutCreateView(BranchPermissionMixin, CreateView):
    model = PaymentOut
    form_class = PaymentOutForm
    template_name = 'finance/paymentout_form.html'
    success_url = reverse_lazy('paymentout-list')
    required_perm = 'add_paymentout'
    branch_field = 'last_person__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class PaymentOutUpdateView(BranchPermissionMixin, UpdateView):
    model = PaymentOut
    form_class = PaymentOutForm
    template_name = 'finance/paymentout_form.html'
    success_url = reverse_lazy('paymentout-list')
    required_perm = 'change_paymentout'
    branch_field = 'last_person__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class PaymentOutDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = PaymentOut
    template_name = 'finance/paymentout_confirm_delete.html'
    success_url = reverse_lazy('paymentout-list')
    required_perm = 'delete_paymentout'
    branch_field = 'last_person__branch'


# ============================================================
# Deposit Views
# ============================================================

class DepositListView(BranchPermissionMixin, ListView):
    model = Deposit
    template_name = 'finance/deposit_list.html'
    context_object_name = 'deposits'
    paginate_by = 20
    required_perm = 'view_deposit'
    branch_field = 'bank__branch'

    def get_queryset(self):
        queryset = Deposit.objects.select_related('bank', 'last_person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        return queryset


class DepositDetailView(BranchPermissionMixin, DetailView):
    model = Deposit
    template_name = 'finance/deposit_detail.html'
    context_object_name = 'deposit'
    required_perm = 'view_deposit'
    branch_field = 'bank__branch'

    def get_queryset(self):
        return Deposit.objects.select_related('bank', 'last_person')


class DepositCreateView(BranchPermissionMixin, CreateView):
    model = Deposit
    form_class = DepositForm
    template_name = 'finance/deposit_form.html'
    success_url = reverse_lazy('deposit-list')
    required_perm = 'add_deposit'
    branch_field = 'bank__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class DepositUpdateView(BranchPermissionMixin, UpdateView):
    model = Deposit
    form_class = DepositForm
    template_name = 'finance/deposit_form.html'
    success_url = reverse_lazy('deposit-list')
    required_perm = 'change_deposit'
    branch_field = 'bank__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class DepositDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = Deposit
    template_name = 'finance/deposit_confirm_delete.html'
    success_url = reverse_lazy('deposit-list')
    required_perm = 'delete_deposit'
    branch_field = 'bank__branch'


# ============================================================
# Withdraw Views
# ============================================================

class WithdrawListView(BranchPermissionMixin, ListView):
    model = Withdraw
    template_name = 'finance/withdraw_list.html'
    context_object_name = 'withdraws'
    paginate_by = 20
    required_perm = 'view_withdraw'
    branch_field = 'bank__branch'

    def get_queryset(self):
        queryset = Withdraw.objects.select_related('bank', 'last_person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        return queryset


class WithdrawDetailView(BranchPermissionMixin, DetailView):
    model = Withdraw
    template_name = 'finance/withdraw_detail.html'
    context_object_name = 'withdraw'
    required_perm = 'view_withdraw'
    branch_field = 'bank__branch'

    def get_queryset(self):
        return Withdraw.objects.select_related('bank', 'last_person')


class WithdrawCreateView(BranchPermissionMixin, CreateView):
    model = Withdraw
    form_class = WithdrawForm
    template_name = 'finance/withdraw_form.html'
    success_url = reverse_lazy('withdraw-list')
    required_perm = 'add_withdraw'
    branch_field = 'bank__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class WithdrawUpdateView(BranchPermissionMixin, UpdateView):
    model = Withdraw
    form_class = WithdrawForm
    template_name = 'finance/withdraw_form.html'
    success_url = reverse_lazy('withdraw-list')
    required_perm = 'change_withdraw'
    branch_field = 'bank__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class WithdrawDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = Withdraw
    template_name = 'finance/withdraw_confirm_delete.html'
    success_url = reverse_lazy('withdraw-list')
    required_perm = 'delete_withdraw'
    branch_field = 'bank__branch'


# ============================================================
# BillBuyType Views
# ============================================================

class BillBuyTypeListView(BranchPermissionMixin, ListView):
    model = BillBuyType
    template_name = 'finance/billbuytype_list.html'
    context_object_name = 'bill_buy_types'
    paginate_by = 20
    required_perm = 'view_billbuytype'


class BillBuyTypeDetailView(BranchPermissionMixin, DetailView):
    model = BillBuyType
    template_name = 'finance/billbuytype_detail.html'
    context_object_name = 'bill_buy_type'
    required_perm = 'view_billbuytype'


class BillBuyTypeCreateView(BranchPermissionMixin, CreateView):
    model = BillBuyType
    form_class = BillBuyTypeForm
    template_name = 'finance/billbuytype_form.html'
    success_url = reverse_lazy('billbuytype-list')
    required_perm = 'add_billbuytype'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class BillBuyTypeUpdateView(BranchPermissionMixin, UpdateView):
    model = BillBuyType
    form_class = BillBuyTypeForm
    template_name = 'finance/billbuytype_form.html'
    success_url = reverse_lazy('billbuytype-list')
    required_perm = 'change_billbuytype'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class BillBuyTypeDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = BillBuyType
    template_name = 'finance/billbuytype_confirm_delete.html'
    success_url = reverse_lazy('billbuytype-list')
    required_perm = 'delete_billbuytype'


# ============================================================
# BillBuy Views
# ============================================================

class BillBuyListView(BranchPermissionMixin, ListView):
    model = BillBuy
    template_name = 'finance/billbuy_list.html'
    context_object_name = 'bill_buys'
    paginate_by = 20
    required_perm = 'view_billbuy'
    branch_field = 'last_person__branch'

    def get_queryset(self):
        queryset = BillBuy.objects.select_related('bill_buy_type', 'last_person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        return queryset


class BillBuyDetailView(BranchPermissionMixin, DetailView):
    model = BillBuy
    template_name = 'finance/billbuy_detail.html'
    context_object_name = 'bill_buy'
    required_perm = 'view_billbuy'
    branch_field = 'last_person__branch'

    def get_queryset(self):
        return BillBuy.objects.select_related('bill_buy_type', 'last_person')


class BillBuyCreateView(BranchPermissionMixin, CreateView):
    model = BillBuy
    form_class = BillBuyForm
    template_name = 'finance/billbuy_form.html'
    success_url = reverse_lazy('billbuy-list')
    required_perm = 'add_billbuy'
    branch_field = 'last_person__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class BillBuyUpdateView(BranchPermissionMixin, UpdateView):
    model = BillBuy
    form_class = BillBuyForm
    template_name = 'finance/billbuy_form.html'
    success_url = reverse_lazy('billbuy-list')
    required_perm = 'change_billbuy'
    branch_field = 'last_person__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class BillBuyDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = BillBuy
    template_name = 'finance/billbuy_confirm_delete.html'
    success_url = reverse_lazy('billbuy-list')
    required_perm = 'delete_billbuy'
    branch_field = 'last_person__branch'


# ============================================================
# Offer Views
# ============================================================

class OfferListView(BranchPermissionMixin, ListView):
    model = Offer
    template_name = 'finance/offer_list.html'
    context_object_name = 'offers'
    paginate_by = 20
    required_perm = 'view_offer_price'
    branch_field = 'master__branch'

    def get_queryset(self):
        queryset = Offer.objects.select_related('master', 'master__branch', 'last_person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(customer_name__icontains=search)
        master = self.request.GET.get('master')
        if master:
            queryset = queryset.filter(master_id=master)
        registered = self.request.GET.get('registered')
        if registered is not None:
            queryset = queryset.filter(registered=registered.lower() == 'true')
        return queryset


class OfferDetailView(BranchPermissionMixin, DetailView):
    model = Offer
    template_name = 'finance/offer_detail.html'
    context_object_name = 'offer'
    required_perm = 'view_offer_price'
    branch_field = 'master__branch'

    def get_queryset(self):
        return Offer.objects.select_related('master', 'master__branch', 'last_person')


class OfferCreateView(BranchPermissionMixin, CreateView):
    model = Offer
    form_class = OfferForm
    template_name = 'finance/offer_form.html'
    success_url = reverse_lazy('offer-list')
    required_perm = 'add_offer_price'
    branch_field = 'master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class OfferUpdateView(BranchPermissionMixin, UpdateView):
    model = Offer
    form_class = OfferForm
    template_name = 'finance/offer_form.html'
    success_url = reverse_lazy('offer-list')
    required_perm = 'change_offer_price'
    branch_field = 'master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class OfferDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = Offer
    template_name = 'finance/offer_confirm_delete.html'
    success_url = reverse_lazy('offer-list')
    required_perm = 'delete_offer_price'
    branch_field = 'master__branch'


# ============================================================
# Call Views
# ============================================================

class CallListView(BranchPermissionMixin, ListView):
    model = Call
    template_name = 'finance/call_list.html'
    context_object_name = 'calls'
    paginate_by = 20
    required_perm = 'view_call'
    branch_field = 'offer__master__branch'

    def get_queryset(self):
        queryset = Call.objects.select_related('offer', 'person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        offer = self.request.GET.get('offer')
        if offer:
            queryset = queryset.filter(offer_id=offer)
        person = self.request.GET.get('person')
        if person:
            queryset = queryset.filter(person_id=person)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offers'] = Offer.objects.select_related('master').all()
        return context


class CallDetailView(BranchPermissionMixin, DetailView):
    model = Call
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'finance/call_detail.html'
    context_object_name = 'call'
    required_perm = 'view_call'
    branch_field = 'offer__master__branch'

    def get_queryset(self):
        return Call.objects.select_related('offer', 'person')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offers'] = Offer.objects.select_related('master').all()
        return context


class CallCreateView(BranchPermissionMixin, CreateView):
    model = Call
    form_class = CallForm
    template_name = 'finance/call_form.html'
    success_url = reverse_lazy('call-list')
    required_perm = 'add_call'
    branch_field = 'offer__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.person = self.request.user
        return super().form_valid(form)


class CallUpdateView(BranchPermissionMixin, UpdateView):
    model = Call
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = CallForm
    template_name = 'finance/call_form.html'
    success_url = reverse_lazy('call-list')
    required_perm = 'change_call'
    branch_field = 'offer__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.person = self.request.user
        return super().form_valid(form)


class CallDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = Call
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'finance/call_confirm_delete.html'
    success_url = reverse_lazy('call-list')
    required_perm = 'delete_call'
    branch_field = 'offer__master__branch'


@require_POST
def call_create_ajax(request):
    if not request.user.has_perm_on_any_branch('add_call'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = CallForm(request.POST, user=request.user)
    if form.is_valid():
        call = form.save(commit=False)
        call.person = request.user
        call.save()
        return JsonResponse({'success': True, 'message': 'تم إنشاء المكالمة بنجاح', 'id': call.id, 'slug': call.slug})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@require_POST
def call_update_ajax(request, pk):
    call = get_object_or_404(Call, pk=pk)
    if not request.user.has_perm('change_call', branch=call.offer.master.branch):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = CallForm(request.POST, instance=call, user=request.user)
    if form.is_valid():
        call = form.save(commit=False)
        call.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث المكالمة بنجاح'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ============================================================
# DisbursementRequest (إذن الصرف) Views
# ============================================================

class DisbursementListView(BranchPermissionMixin, ListView):
    model = DisbursementRequest
    template_name = 'finance/disbursement_list.html'
    context_object_name = 'disbursements'
    paginate_by = 20
    required_perm = 'view_disbursementrequest'
    branch_field = 'last_person__branch'

    def get_queryset(self):
        qs = DisbursementRequest.objects.select_related('last_person', 'approved_by').all()
        qs = filter_by_branch(qs, self.request.user, self.branch_field, perm=self.required_perm)
        search = self.request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(entity_name__icontains=search)
                | Q(requester_name__icontains=search)
                | Q(request_number__icontains=search)
            )
        status = self.request.GET.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = DisbursementStatus.choices
        return context


class DisbursementDetailView(BranchPermissionMixin, DetailView):
    model = DisbursementRequest
    template_name = 'finance/disbursement_detail.html'
    context_object_name = 'disbursement'
    required_perm = 'view_disbursementrequest'
    branch_field = 'last_person__branch'

    def get_queryset(self):
        return DisbursementRequest.objects.select_related('last_person', 'approved_by', 'created_by')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.object.can_user_edit(self.request.user)
        context['can_approve'] = self.object.can_user_approve(self.request.user)
        return context


class DisbursementCreateView(BranchPermissionMixin, CreateView):
    model = DisbursementRequest
    form_class = DisbursementRequestForm
    template_name = 'finance/disbursement_form.html'
    required_perm = 'add_disbursementrequest'
    branch_field = 'last_person__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['details'] = DisbursementDetailFormSet(self.request.POST, instance=self.object, prefix='details')
        else:
            context['details'] = DisbursementDetailFormSet(instance=self.object, prefix='details')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        details = context['details']
        if not details.is_valid():
            return self.render_to_response(context)
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.last_person = self.request.user
        self.object.save()
        details.instance = self.object
        details.save()
        messages.success(self.request, f'تم إنشاء إذن الصرف رقم {self.object.request_number} بنجاح.')
        return redirect('disbursement-detail', pk=self.object.pk)


class DisbursementUpdateView(BranchPermissionMixin, UpdateView):
    model = DisbursementRequest
    form_class = DisbursementRequestForm
    template_name = 'finance/disbursement_form.html'
    required_perm = 'view_disbursementrequest'
    branch_field = 'last_person__branch'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك تعديل إذن الصرف هذا.')
        if not obj.is_editable():
            messages.error(request, 'لا يمكن تعديل إذن صرف في حالته الحالية.')
            return redirect('disbursement-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['details'] = DisbursementDetailFormSet(self.request.POST, instance=self.object, prefix='details')
        else:
            context['details'] = DisbursementDetailFormSet(instance=self.object, prefix='details')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        details = context['details']
        if not details.is_valid():
            return self.render_to_response(context)
        self.object = form.save(commit=False)
        self.object.last_person = self.request.user
        self.object.save()
        details.instance = self.object
        details.save()
        messages.success(self.request, f'تم تحديث إذن الصرف رقم {self.object.request_number} بنجاح.')
        return redirect('disbursement-detail', pk=self.object.pk)


class DisbursementDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = DisbursementRequest
    template_name = 'finance/disbursement_confirm_delete.html'
    success_url = reverse_lazy('disbursement-list')
    required_perm = 'view_disbursementrequest'
    branch_field = 'last_person__branch'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        can_delete = (
            request.user.is_executive()
            or (obj.created_by_id and obj.created_by_id == request.user.pk)
            or request.user.has_perm('delete_disbursementrequest', branch=obj.branch)
        )
        if not can_delete:
            raise PermissionDenied('غير مسموح لك حذف إذن الصرف هذا.')
        if not obj.is_editable():
            messages.error(request, 'لا يمكن حذف إذن صرف في حالته الحالية.')
            return redirect('disbursement-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)


@login_required
@require_POST
def disbursement_transition(request, pk, action):
    disbursement = get_object_or_404(DisbursementRequest, pk=pk)
    if action == 'submit':
        if not disbursement.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if disbursement.status not in disbursement.SUBMITTABLE_STATUSES:
            messages.error(request, 'لا يمكن إرسال إذن الصرف للاعتماد في حالته الحالية.')
            return redirect('disbursement-detail', pk=disbursement.pk)
        disbursement.status = DisbursementStatus.PENDING
        disbursement.submitted_at = timezone.now()
        disbursement.rejection_reason = ''
        disbursement.save()
        messages.success(request, 'تم إرسال إذن الصرف بانتظار الاعتماد.')
    elif action == 'approve':
        if not disbursement.can_user_approve(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if disbursement.status != DisbursementStatus.PENDING:
            messages.error(request, 'لا يمكن اعتماد إذن صرف ليس بانتظار الاعتماد.')
            return redirect('disbursement-detail', pk=disbursement.pk)
        disbursement.status = DisbursementStatus.APPROVED
        disbursement.approved_by = request.user
        disbursement.approved_at = timezone.now()
        disbursement.save()
        messages.success(request, 'تم اعتماد إذن الصرف بنجاح.')
    elif action == 'reject':
        if not disbursement.can_user_approve(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if disbursement.status != DisbursementStatus.PENDING:
            messages.error(request, 'لا يمكن رفض إذن صرف ليس بانتظار الاعتماد.')
            return redirect('disbursement-detail', pk=disbursement.pk)
        reason = (request.POST.get('rejection_reason') or '').strip()
        if not reason:
            messages.error(request, 'يجب إدخال سبب الرفض.')
            return redirect('disbursement-detail', pk=disbursement.pk)
        disbursement.status = DisbursementStatus.REJECTED
        disbursement.rejection_reason = reason
        disbursement.save()
        messages.success(request, 'تم رفض إذن الصرف.')
    elif action == 'reopen':
        if not disbursement.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if disbursement.status != DisbursementStatus.REJECTED:
            messages.error(request, 'لا يمكن إعادة فتح إذن صرف غير مرفوض.')
            return redirect('disbursement-detail', pk=disbursement.pk)
        disbursement.status = DisbursementStatus.DRAFT
        disbursement.save()
        messages.success(request, 'تمت إعادة إذن الصرف كمسودة للتعديل.')
    return redirect('disbursement-detail', pk=disbursement.pk)
