from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.mixins import BranchPermissionMixin, ProtectedDeleteMixin, filter_by_branch
from .forms import DisbursementRequestForm, DisbursementDetailFormSet
from .models import DisbursementRequest, DisbursementStatus


# ============================================================
# إذن الصرف
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
        context['can_update'] = self.object.can_user_update(self.request.user)
        return context


class DisbursementCreateView(BranchPermissionMixin, CreateView):
    model = DisbursementRequest
    form_class = DisbursementRequestForm
    template_name = 'finance/disbursement_form.html'
    required_perm = 'add_disbursementrequest'
    branch_field = 'last_person__branch'

    def get_initial(self):
        initial = super().get_initial()
        user = self.request.user
        full_name = ' '.join(user.get_full_name().split())
        initial['requester_name'] = full_name
        initial['requester_signed_name'] = full_name
        role = user.employee_roles.select_related('role').first()
        if role:
            initial['requester_job_title'] = role.role.name
        return initial

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
        if not (self.request.user.is_executive() or self.request.user.has_perm_on_any_branch(DisbursementRequest.approve_perm)):
            self.object.supervisor_name = ''
            self.object.supervisor_signed_name = ''
            self.object.supervisor_signature_date = None
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
        if not (obj.can_user_edit(request.user) or obj.can_user_approve(request.user)):
            raise PermissionDenied('غير مسموح لك تعديل إذن الصرف هذا.')
        if not obj.can_user_update(request.user):
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
        if not self.object.can_user_approve(self.request.user):
            original = DisbursementRequest.objects.get(pk=self.object.pk)
            for f in DisbursementRequestForm.SUPERVISOR_FIELDS:
                setattr(self.object, f, getattr(original, f))
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
        approver_name = ' '.join(request.user.get_full_name().split()) or request.user.email
        disbursement.supervisor_name = approver_name
        disbursement.supervisor_signed_name = approver_name
        disbursement.supervisor_signature_date = timezone.now().date()
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
