from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from accounts.mixins import BranchPermissionMixin, filter_by_branch
from courses.models import Course
from students.models import Student
from prospects.models import Prospect
from prospects.utils import get_user_root_branch_ids, is_root_branch, do_convert_prospect_to_student
from .models import Account, AttachType, Attach, AccountAttach, AccountCondition, AccountNote
from .forms import (
    AccountForm, AttachTypeForm, AttachForm,
    AccountAttachForm, AccountConditionForm, AccountNoteForm,
)


# ============================================================
# Account Views
# ============================================================

class AccountListView(BranchPermissionMixin, ListView):
    model = Account
    template_name = 'registrations/account_list.html'
    context_object_name = 'accounts'
    paginate_by = 20
    required_perm = 'view_registration'
    branch_field = 'course__master__branch'

    def get_queryset(self):
        queryset = Account.objects.select_related('student', 'course', 'course__master', 'last_person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(student__contact__first_name__icontains=search) |
                Q(student__contact__forth_name__icontains=search)
            )
        course = self.request.GET.get('course')
        if course:
            queryset = queryset.filter(course_id=course)
        student = self.request.GET.get('student')
        if student:
            queryset = queryset.filter(student_id=student)
        payment_type = self.request.GET.get('payment_type')
        if payment_type:
            queryset = queryset.filter(course_payment_type=payment_type)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.select_related('master').all()
        context['students'] = Student.objects.select_related('contact').all()
        root_ids = get_user_root_branch_ids(self.request.user, 'add_registration')
        context['prospects'] = Prospect.objects.filter(
            student__isnull=True, branch_id__in=root_ids
        ).order_by('-created_at')
        context['is_root_company'] = bool(root_ids)
        return context


class AccountDetailView(BranchPermissionMixin, DetailView):
    model = Account
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'registrations/account_detail.html'
    context_object_name = 'account'
    required_perm = 'view_registration'
    branch_field = 'course__master__branch'

    def get_queryset(self):
        return Account.objects.select_related('student', 'course', 'course__master', 'last_person')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.select_related('master').all()
        context['students'] = Student.objects.select_related('contact').all()
        return context


class AccountCreateView(BranchPermissionMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'registrations/account_form.html'
    success_url = reverse_lazy('registration-list')
    required_perm = 'add_registration'
    branch_field = 'course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        prospect = form.cleaned_data.get('prospect')
        course = form.cleaned_data.get('course')
        if prospect and course and course.master and course.master.branch and is_root_branch(course.master.branch):
            student = do_convert_prospect_to_student(prospect, self.request.user)
            form.instance.student = student
        return super().form_valid(form)


class AccountUpdateView(BranchPermissionMixin, UpdateView):
    model = Account
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    form_class = AccountForm
    template_name = 'registrations/account_form.html'
    success_url = reverse_lazy('registration-list')
    required_perm = 'change_registration'
    branch_field = 'course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        return super().form_valid(form)


class AccountDeleteView(BranchPermissionMixin, DeleteView):
    model = Account
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    template_name = 'registrations/account_confirm_delete.html'
    success_url = reverse_lazy('registration-list')
    required_perm = 'delete_registration'
    branch_field = 'course__master__branch'

    def delete(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except ProtectedError:
            messages.error(request, 'لا يمكن حذف التسجيل لأنه مرتبط بمدفوعات. احذف المدفوعات الأول.')
            return redirect(self.success_url)


@login_required
@require_POST
def account_create_ajax(request):
    if not request.user.has_perm_on_any_branch('add_registration'):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = AccountForm(request.POST, user=request.user)
    if form.is_valid():
        account = form.save(commit=False)
        account.last_person = request.user

        # في شركة الجذور، المستفسر بيتحول لطالب قبل التسجيل
        prospect = form.cleaned_data.get('prospect')
        course = form.cleaned_data.get('course')
        if prospect and course and course.master and course.master.branch and is_root_branch(course.master.branch):
            student = do_convert_prospect_to_student(prospect, request.user)
            account.student = student

        account.save()
        return JsonResponse({'success': True, 'message': 'تم إنشاء التسجيل بنجاح', 'id': account.id, 'slug': account.slug})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_POST
def account_update_ajax(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if not request.user.has_perm('change_registration', branch=account.course.master.branch):
        return JsonResponse({'success': False, 'message': 'غير مسموح لك دخول هنا'}, status=403)
    form = AccountForm(request.POST, instance=account, user=request.user)
    if form.is_valid():
        account = form.save(commit=False)
        account.last_person = request.user
        account.save()
        return JsonResponse({'success': True, 'message': 'تم تحديث التسجيل بنجاح'})
    return JsonResponse({'success': False, 'errors': form.errors}, status=400)


# ============================================================
# AttachType Views
# ============================================================

class AttachTypeListView(BranchPermissionMixin, ListView):
    model = AttachType
    template_name = 'registrations/attachtype_list.html'
    context_object_name = 'attach_types'
    paginate_by = 20
    required_perm = 'view_attachtype'


class AttachTypeDetailView(BranchPermissionMixin, DetailView):
    model = AttachType
    template_name = 'registrations/attachtype_detail.html'
    context_object_name = 'attach_type'
    required_perm = 'view_attachtype'


class AttachTypeCreateView(BranchPermissionMixin, CreateView):
    model = AttachType
    form_class = AttachTypeForm
    template_name = 'registrations/attachtype_form.html'
    success_url = reverse_lazy('attachtype-list')
    required_perm = 'add_attachtype'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class AttachTypeUpdateView(BranchPermissionMixin, UpdateView):
    model = AttachType
    form_class = AttachTypeForm
    template_name = 'registrations/attachtype_form.html'
    success_url = reverse_lazy('attachtype-list')
    required_perm = 'change_attachtype'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class AttachTypeDeleteView(BranchPermissionMixin, DeleteView):
    model = AttachType
    template_name = 'registrations/attachtype_confirm_delete.html'
    success_url = reverse_lazy('attachtype-list')
    required_perm = 'delete_attachtype'


# ============================================================
# Attach Views
# ============================================================

class AttachListView(BranchPermissionMixin, ListView):
    model = Attach
    template_name = 'registrations/attach_list.html'
    context_object_name = 'attaches'
    paginate_by = 20
    required_perm = 'view_attach'
    branch_field = 'person__branch'

    def get_queryset(self):
        queryset = Attach.objects.select_related('attach_type', 'person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        attach_type = self.request.GET.get('type')
        if attach_type:
            queryset = queryset.filter(attach_type_id=attach_type)
        return queryset


class AttachDetailView(BranchPermissionMixin, DetailView):
    model = Attach
    template_name = 'registrations/attach_detail.html'
    context_object_name = 'attach'
    required_perm = 'view_attach'
    branch_field = 'person__branch'

    def get_queryset(self):
        return Attach.objects.select_related('attach_type', 'person')


class AttachCreateView(BranchPermissionMixin, CreateView):
    model = Attach
    form_class = AttachForm
    template_name = 'registrations/attach_form.html'
    success_url = reverse_lazy('attach-list')
    required_perm = 'add_attach'
    branch_field = 'person__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.person = self.request.user
        return super().form_valid(form)


class AttachUpdateView(BranchPermissionMixin, UpdateView):
    model = Attach
    form_class = AttachForm
    template_name = 'registrations/attach_form.html'
    success_url = reverse_lazy('attach-list')
    required_perm = 'change_attach'
    branch_field = 'person__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class AttachDeleteView(BranchPermissionMixin, DeleteView):
    model = Attach
    template_name = 'registrations/attach_confirm_delete.html'
    success_url = reverse_lazy('attach-list')
    required_perm = 'delete_attach'
    branch_field = 'person__branch'


# ============================================================
# AccountAttach Views
# ============================================================

class AccountAttachListView(BranchPermissionMixin, ListView):
    model = AccountAttach
    template_name = 'registrations/accountattach_list.html'
    context_object_name = 'account_attaches'
    paginate_by = 20
    required_perm = 'view_accountattach'
    branch_field = 'account__course__master__branch'

    def get_queryset(self):
        queryset = AccountAttach.objects.select_related('account', 'attach').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        account = self.request.GET.get('account')
        if account:
            queryset = queryset.filter(account_id=account)
        return queryset


class AccountAttachDetailView(BranchPermissionMixin, DetailView):
    model = AccountAttach
    template_name = 'registrations/accountattach_detail.html'
    context_object_name = 'account_attach'
    required_perm = 'view_accountattach'
    branch_field = 'account__course__master__branch'

    def get_queryset(self):
        return AccountAttach.objects.select_related('account', 'attach')


class AccountAttachCreateView(BranchPermissionMixin, CreateView):
    model = AccountAttach
    form_class = AccountAttachForm
    template_name = 'registrations/accountattach_form.html'
    success_url = reverse_lazy('accountattach-list')
    required_perm = 'add_accountattach'
    branch_field = 'account__course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class AccountAttachUpdateView(BranchPermissionMixin, UpdateView):
    model = AccountAttach
    form_class = AccountAttachForm
    template_name = 'registrations/accountattach_form.html'
    success_url = reverse_lazy('accountattach-list')
    required_perm = 'change_accountattach'
    branch_field = 'account__course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class AccountAttachDeleteView(BranchPermissionMixin, DeleteView):
    model = AccountAttach
    template_name = 'registrations/accountattach_confirm_delete.html'
    success_url = reverse_lazy('accountattach-list')
    required_perm = 'delete_accountattach'
    branch_field = 'account__course__master__branch'


# ============================================================
# AccountCondition Views
# ============================================================

class AccountConditionListView(BranchPermissionMixin, ListView):
    model = AccountCondition
    template_name = 'registrations/accountcondition_list.html'
    context_object_name = 'account_conditions'
    paginate_by = 20
    required_perm = 'view_accountcondition'
    branch_field = 'account__course__master__branch'

    def get_queryset(self):
        queryset = AccountCondition.objects.select_related('account', 'person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        account = self.request.GET.get('account')
        if account:
            queryset = queryset.filter(account_id=account)
        fulfilled = self.request.GET.get('fulfilled')
        if fulfilled is not None:
            queryset = queryset.filter(fulfilled=fulfilled.lower() == 'true')
        return queryset


class AccountConditionDetailView(BranchPermissionMixin, DetailView):
    model = AccountCondition
    template_name = 'registrations/accountcondition_detail.html'
    context_object_name = 'account_condition'
    required_perm = 'view_accountcondition'
    branch_field = 'account__course__master__branch'

    def get_queryset(self):
        return AccountCondition.objects.select_related('account', 'person')


class AccountConditionCreateView(BranchPermissionMixin, CreateView):
    model = AccountCondition
    form_class = AccountConditionForm
    template_name = 'registrations/accountcondition_form.html'
    success_url = reverse_lazy('accountcondition-list')
    required_perm = 'add_accountcondition'
    branch_field = 'account__course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.person = self.request.user
        return super().form_valid(form)


class AccountConditionUpdateView(BranchPermissionMixin, UpdateView):
    model = AccountCondition
    form_class = AccountConditionForm
    template_name = 'registrations/accountcondition_form.html'
    success_url = reverse_lazy('accountcondition-list')
    required_perm = 'change_accountcondition'
    branch_field = 'account__course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.person = self.request.user
        return super().form_valid(form)


class AccountConditionDeleteView(BranchPermissionMixin, DeleteView):
    model = AccountCondition
    template_name = 'registrations/accountcondition_confirm_delete.html'
    success_url = reverse_lazy('accountcondition-list')
    required_perm = 'delete_accountcondition'
    branch_field = 'account__course__master__branch'


# ============================================================
# AccountNote Views
# ============================================================

class AccountNoteListView(BranchPermissionMixin, ListView):
    model = AccountNote
    template_name = 'registrations/accountnote_list.html'
    context_object_name = 'account_notes'
    paginate_by = 20
    required_perm = 'view_accountnote'
    branch_field = 'account__course__master__branch'

    def get_queryset(self):
        queryset = AccountNote.objects.select_related('account', 'person').all()
        queryset = filter_by_branch(queryset, self.request.user, self.branch_field, perm=self.required_perm)
        account = self.request.GET.get('account')
        if account:
            queryset = queryset.filter(account_id=account)
        return queryset


class AccountNoteDetailView(BranchPermissionMixin, DetailView):
    model = AccountNote
    template_name = 'registrations/accountnote_detail.html'
    context_object_name = 'account_note'
    required_perm = 'view_accountnote'
    branch_field = 'account__course__master__branch'

    def get_queryset(self):
        return AccountNote.objects.select_related('account', 'person')


class AccountNoteCreateView(BranchPermissionMixin, CreateView):
    model = AccountNote
    form_class = AccountNoteForm
    template_name = 'registrations/accountnote_form.html'
    success_url = reverse_lazy('accountnote-list')
    required_perm = 'add_accountnote'
    branch_field = 'account__course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.person = self.request.user
        return super().form_valid(form)


class AccountNoteUpdateView(BranchPermissionMixin, UpdateView):
    model = AccountNote
    form_class = AccountNoteForm
    template_name = 'registrations/accountnote_form.html'
    success_url = reverse_lazy('accountnote-list')
    required_perm = 'change_accountnote'
    branch_field = 'account__course__master__branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.person = self.request.user
        return super().form_valid(form)


class AccountNoteDeleteView(BranchPermissionMixin, DeleteView):
    model = AccountNote
    template_name = 'registrations/accountnote_confirm_delete.html'
    success_url = reverse_lazy('accountnote-list')
    required_perm = 'delete_accountnote'
    branch_field = 'account__course__master__branch'
