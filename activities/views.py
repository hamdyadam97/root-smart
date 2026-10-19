from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.mixins import BranchPermissionMixin, ProtectedDeleteMixin, filter_by_branch
from .forms import (
    ActivityForm, FinancialAnalysisForm, ActivityCoordinationForm, FinalFinancialAnalysisForm,
)
from .models import (
    Activity, FinancialAnalysis, ActivityCoordination, FinalFinancialAnalysis, ActivityLog, StageStatus,
    ActivityEnrollment,
)
from .pdf_utils import (
    build_activity_pdf, build_financial_pdf, build_coordination_pdf, build_final_pdf,
)


def _log(activity, stage, action, user, notes=''):
    ActivityLog.objects.create(
        activity=activity, stage=stage, action=action, person=user, notes=notes
    )


def _get_activity_or_denied(user, activity_pk):
    """الوصول للنشاط: المنشئ، أو من يملك صلاحية عرض الأنشطة على الفرع، أو المدير التنفيذي."""
    activity = get_object_or_404(Activity, pk=activity_pk)
    if user.is_executive():
        return activity
    if activity.created_by_id and activity.created_by_id == user.pk:
        return activity
    if user.has_perm('view_activity', branch=activity.branch):
        return activity
    raise PermissionDenied('غير مسموح لك دخول هنا')


def _parent_activity(obj):
    """النشاط الأب للنموذج — النموذج نفسه إذا كان عقد النشاط."""
    return getattr(obj, 'activity', obj)


def _apply_submit_action(request, obj, stage):
    """معالجة زر الحفظ في نماذج المراحل: حفظ / حفظ كمكتمل / حفظ وإرسال للاعتماد."""
    action = request.POST.get('submit_action', 'save')
    if action == 'complete':
        obj.status = StageStatus.COMPLETED
        obj.save()
    elif action == 'submit':
        if obj.status not in obj.SUBMITTABLE_STATUSES:
            messages.error(request, 'لا يمكن إرسال النموذج للاعتماد في حالته الحالية.')
            return
        obj.status = StageStatus.PENDING
        obj.submitted_at = timezone.now()
        obj.rejection_reason = ''
        obj.save()
        _log(_parent_activity(obj), stage, 'submit', request.user)
        messages.success(request, 'تم حفظ النموذج وإرساله بانتظار الاعتماد.')


def _do_transition(request, obj, stage, action):
    """تنفيذ انتقالات الحالة من أزرار صفحة التفاصيل."""
    if action == 'submit':
        if not obj.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if obj.status not in obj.SUBMITTABLE_STATUSES:
            messages.error(request, 'لا يمكن إرسال النموذج للاعتماد في حالته الحالية.')
            return
        obj.status = StageStatus.PENDING
        obj.submitted_at = timezone.now()
        obj.rejection_reason = ''
        obj.save()
        _log(_parent_activity(obj), stage, 'submit', request.user)
        messages.success(request, 'تم إرسال النموذج بانتظار الاعتماد.')
    elif action == 'approve':
        if not obj.can_user_approve(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if obj.status != StageStatus.PENDING:
            messages.error(request, 'لا يمكن اعتماد نموذج ليس بانتظار الاعتماد.')
            return
        obj.status = StageStatus.APPROVED
        obj.approved_by = request.user
        obj.approved_at = timezone.now()
        obj.save()
        _log(_parent_activity(obj), stage, 'approve', request.user)
        messages.success(request, 'تم اعتماد النموذج بنجاح.')
    elif action == 'reject':
        if not obj.can_user_approve(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if obj.status != StageStatus.PENDING:
            messages.error(request, 'لا يمكن رفض نموذج ليس بانتظار الاعتماد.')
            return
        reason = (request.POST.get('rejection_reason') or '').strip()
        if not reason:
            messages.error(request, 'يجب إدخال سبب الرفض.')
            return
        obj.status = StageStatus.REJECTED
        obj.rejection_reason = reason
        obj.save()
        _log(_parent_activity(obj), stage, 'reject', request.user, notes=reason)
        messages.success(request, 'تم رفض النموذج.')
    elif action == 'reopen':
        if not obj.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if obj.status != StageStatus.REJECTED:
            messages.error(request, 'لا يمكن إعادة فتح نموذج غير مرفوض.')
            return
        obj.status = StageStatus.DRAFT
        obj.save()
        _log(_parent_activity(obj), stage, 'reopen', request.user)
        messages.success(request, 'تمت إعادة النموذج كمسودة للتعديل.')


class ActivityListView(BranchPermissionMixin, ListView):
    model = Activity
    template_name = 'activities/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 20
    required_perm = 'view_activity'
    branch_field = 'branch'

    def get_queryset(self):
        qs = Activity.objects.select_related('branch', 'branch__company', 'created_by').all()
        qs = filter_by_branch(qs, self.request.user, 'branch', perm=self.required_perm)
        # المراحل اللاحقة علاقة OneToOne — تُحمّل باستعلام واحد لكل صف
        qs = qs.select_related('financial', 'coordination', 'final_financial')

        search = self.request.GET.get('search', '').strip()
        if search:
            if search.isdigit():
                qs = qs.filter(
                    Q(name__icontains=search)
                    | Q(request_number__icontains=search)
                    | Q(form_number=int(search))
                )
            else:
                qs = qs.filter(Q(name__icontains=search) | Q(request_number__icontains=search))
        status = self.request.GET.get('status', '').strip()
        if status:
            qs = qs.filter(status=status)
        activity_type = self.request.GET.get('activity_type', '').strip()
        if activity_type:
            qs = qs.filter(activity_type=activity_type)
        region = self.request.GET.get('region', '').strip()
        if region:
            qs = qs.filter(region=region)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = StageStatus.choices
        context['activity_type_choices'] = Activity.ACTIVITY_TYPE_CHOICES
        context['region_choices'] = Activity.REGION_CHOICES
        return context


class ActivityDetailView(BranchPermissionMixin, DetailView):
    model = Activity
    template_name = 'activities/activity_detail.html'
    context_object_name = 'activity'
    required_perm = 'view_activity'
    branch_field = 'branch'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activity = self.object
        user = self.request.user
        context['financial'] = FinancialAnalysis.objects.filter(activity=activity).first()
        context['coordination'] = ActivityCoordination.objects.filter(activity=activity).first()
        context['final_financial'] = FinalFinancialAnalysis.objects.filter(activity=activity).first()
        context['logs'] = activity.logs.select_related('person')[:50]
        context['stage_statuses'] = StageStatus
        context['can_edit_activity'] = activity.can_user_edit(user)
        context['can_approve_activity'] = activity.can_user_approve(user)
        context['enrollments'] = activity.enrollments.select_related('student', 'student__contact', 'created_by')
        from students.models import Student
        enrolled_ids = activity.enrollments.values_list('student_id', flat=True)
        context['branch_students'] = Student.objects.filter(
            branch=activity.branch
        ).exclude(pk__in=enrolled_ids).select_related('contact').order_by('contact__first_name')
        if context['financial']:
            context['can_edit_financial'] = context['financial'].can_user_edit(user)
            context['can_approve_financial'] = context['financial'].can_user_approve(user)
        if context['coordination']:
            context['can_edit_coordination'] = context['coordination'].can_user_edit(user)
            context['can_approve_coordination'] = context['coordination'].can_user_approve(user)
        if context['final_financial']:
            context['can_edit_final'] = context['final_financial'].can_user_edit(user)
            context['can_approve_final'] = context['final_financial'].can_user_approve(user)
        return context


class ActivityCreateView(BranchPermissionMixin, CreateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    required_perm = 'add_activity'
    branch_field = 'branch'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('activity-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.last_person = self.request.user
        response = super().form_valid(form)
        _apply_submit_action(self.request, form.instance, 'contract')
        _log(form.instance, 'contract', 'create', self.request.user)
        messages.success(self.request, f'تم إنشاء النشاط "{form.instance.name}" بنجاح.')
        return response


class ActivityUpdateView(BranchPermissionMixin, UpdateView):
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    required_perm = 'view_activity'
    branch_field = 'branch'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك تعديل هذا النشاط.')
        if not obj.is_editable():
            messages.error(request, 'لا يمكن تعديل نموذج في حالته الحالية.')
            return redirect('activity-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('activity-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        response = super().form_valid(form)
        _apply_submit_action(self.request, form.instance, 'contract')
        _log(form.instance, 'contract', 'update', self.request.user)
        messages.success(self.request, 'تم تحديث عقد النشاط بنجاح.')
        return response


class ActivityDeleteView(ProtectedDeleteMixin, BranchPermissionMixin, DeleteView):
    model = Activity
    template_name = 'activities/activity_confirm_delete.html'
    success_url = '/activities/'
    required_perm = 'view_activity'
    branch_field = 'branch'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        can_delete = (
            request.user.is_executive()
            or (obj.created_by_id and obj.created_by_id == request.user.pk)
            or request.user.has_perm('delete_activity', branch=obj.branch)
        )
        if not can_delete:
            raise PermissionDenied('غير مسموح لك حذف هذا النشاط.')
        if not obj.is_editable():
            messages.error(request, 'لا يمكن حذف نموذج في حالته الحالية.')
            return redirect('activity-detail', pk=obj.pk)
        if (FinancialAnalysis.objects.filter(activity=obj).exists()
                or ActivityCoordination.objects.filter(activity=obj).exists()
                or FinalFinancialAnalysis.objects.filter(activity=obj).exists()):
            messages.error(request, 'لا يمكن حذف النشاط بعد بدء المراحل اللاحقة له.')
            return redirect('activity-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        # لا يُسجَّل الحذف هنا لأن سجل النشاط يُحذف تلقائيًا معه (CASCADE)
        messages.success(request, f'تم حذف النشاط "{obj.name}".')
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def activity_transition(request, pk, action):
    activity = _get_activity_or_denied(request.user, pk)
    _do_transition(request, activity, 'contract', action)
    return redirect('activity-detail', pk=activity.pk)


@login_required
@require_POST
def enrollment_add(request, pk):
    """إضافة طالب كمشترك في نشاط."""
    activity = _get_activity_or_denied(request.user, pk)
    if not activity.can_user_edit(request.user):
        raise PermissionDenied('غير مسموح لك تعديل هذا النشاط.')
    from students.models import Student
    student = get_object_or_404(Student, pk=request.POST.get('student'))
    enrollment, created = ActivityEnrollment.objects.get_or_create(
        activity=activity, student=student,
        defaults={'created_by': request.user},
    )
    if created:
        _log(activity, 'contract', 'enroll', request.user, notes=student.get_full_name())
        messages.success(request, f'تمت إضافة "{student.get_full_name()}" إلى النشاط.')
    else:
        messages.info(request, 'هذا الطالب مشترك في النشاط بالفعل.')
    return redirect('activity-detail', pk=activity.pk)


@login_required
@require_POST
def enrollment_remove(request, pk, enrollment_pk):
    """إزالة طالب من مشتركي نشاط."""
    activity = _get_activity_or_denied(request.user, pk)
    if not activity.can_user_edit(request.user):
        raise PermissionDenied('غير مسموح لك تعديل هذا النشاط.')
    enrollment = get_object_or_404(ActivityEnrollment, pk=enrollment_pk, activity=activity)
    name = enrollment.student.get_full_name()
    enrollment.delete()
    _log(activity, 'contract', 'unenroll', request.user, notes=name)
    messages.success(request, f'تمت إزالة "{name}" من النشاط.')
    return redirect('activity-detail', pk=activity.pk)


class FinancialCreateView(CreateView):
    model = FinancialAnalysis
    form_class = FinancialAnalysisForm
    template_name = 'activities/financial_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.activity = _get_activity_or_denied(request.user, kwargs['activity_pk'])
        if self.activity.status != StageStatus.APPROVED:
            messages.error(request, 'التحليل المالي لا يُتاح إلا بعد اعتماد عقد النشاط.')
            return redirect('activity-detail', pk=self.activity.pk)
        if not self.activity.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if FinancialAnalysis.objects.filter(activity=self.activity).exists():
            messages.error(request, 'يوجد تحليل مالي مسجل لهذا النشاط بالفعل.')
            return redirect('activity-detail', pk=self.activity.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('activity-detail', kwargs={'pk': self.object.activity_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = self.activity
        return context

    def form_valid(self, form):
        form.instance.activity = self.activity
        form.instance.created_by = self.request.user
        form.instance.last_person = self.request.user
        response = super().form_valid(form)
        _apply_submit_action(self.request, form.instance, 'financial')
        _log(self.activity, 'financial', 'create', self.request.user)
        messages.success(self.request, 'تم إنشاء التحليل المالي بنجاح.')
        return response


class FinancialUpdateView(UpdateView):
    model = FinancialAnalysis
    form_class = FinancialAnalysisForm
    template_name = 'activities/financial_form.html'
    pk_url_kwarg = 'pk'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك تعديل هذا التحليل المالي.')
        if not obj.is_editable():
            messages.error(request, 'لا يمكن تعديل نموذج في حالته الحالية.')
            return redirect('activity-detail', pk=obj.activity_id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        analysis = get_object_or_404(FinancialAnalysis, pk=self.kwargs['pk'])
        _get_activity_or_denied(self.request.user, analysis.activity_id)
        return analysis

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('activity-detail', kwargs={'pk': self.object.activity_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = self.object.activity
        return context

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        response = super().form_valid(form)
        _apply_submit_action(self.request, form.instance, 'financial')
        _log(form.instance.activity, 'financial', 'update', self.request.user)
        messages.success(self.request, 'تم تحديث التحليل المالي بنجاح.')
        return response


class FinancialDeleteView(ProtectedDeleteMixin, DeleteView):
    model = FinancialAnalysis
    template_name = 'activities/financial_confirm_delete.html'

    def get_object(self, queryset=None):
        analysis = get_object_or_404(FinancialAnalysis, pk=self.kwargs['pk'])
        _get_activity_or_denied(self.request.user, analysis.activity_id)
        if not analysis.can_user_edit(self.request.user):
            raise PermissionDenied('غير مسموح لك حذف هذا التحليل المالي.')
        return analysis

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        self.success_url = f'/activities/{obj.activity_id}/'
        if not obj.is_editable():
            messages.error(request, 'لا يمكن حذف نموذج في حالته الحالية.')
            return redirect('activity-detail', pk=obj.activity_id)
        if ActivityCoordination.objects.filter(activity=obj.activity).exists():
            messages.error(request, 'لا يمكن حذف التحليل المالي بعد بدء مرحلة التنسيق والجاهزية.')
            return redirect('activity-detail', pk=obj.activity_id)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        _log(obj.activity, 'financial', 'delete', request.user)
        messages.success(request, 'تم حذف التحليل المالي.')
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def financial_transition(request, pk, action):
    analysis = get_object_or_404(FinancialAnalysis, pk=pk)
    _get_activity_or_denied(request.user, analysis.activity_id)
    _do_transition(request, analysis, 'financial', action)
    return redirect('activity-detail', pk=analysis.activity_id)


class CoordinationCreateView(CreateView):
    model = ActivityCoordination
    form_class = ActivityCoordinationForm
    template_name = 'activities/coordination_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.activity = _get_activity_or_denied(request.user, kwargs['activity_pk'])
        financial = FinancialAnalysis.objects.filter(activity=self.activity).first()
        if not financial or financial.status != StageStatus.APPROVED:
            messages.error(request, 'نموذج التنسيق والجاهزية لا يُتاح إلا بعد اعتماد التحليل المالي.')
            return redirect('activity-detail', pk=self.activity.pk)
        if not self.activity.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if ActivityCoordination.objects.filter(activity=self.activity).exists():
            messages.error(request, 'يوجد نموذج تنسيق مسجل لهذا النشاط بالفعل.')
            return redirect('activity-detail', pk=self.activity.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('activity-detail', kwargs={'pk': self.object.activity_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = self.activity
        return context

    def form_valid(self, form):
        form.instance.activity = self.activity
        form.instance.created_by = self.request.user
        form.instance.last_person = self.request.user
        response = super().form_valid(form)
        _apply_submit_action(self.request, form.instance, 'coordination')
        _log(self.activity, 'coordination', 'create', self.request.user)
        messages.success(self.request, 'تم إنشاء نموذج التنسيق والجاهزية بنجاح.')
        return response


class CoordinationUpdateView(UpdateView):
    model = ActivityCoordination
    form_class = ActivityCoordinationForm
    template_name = 'activities/coordination_form.html'
    pk_url_kwarg = 'pk'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك تعديل هذا النموذج.')
        if not obj.is_editable():
            messages.error(request, 'لا يمكن تعديل نموذج في حالته الحالية.')
            return redirect('activity-detail', pk=obj.activity_id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        coordination = get_object_or_404(ActivityCoordination, pk=self.kwargs['pk'])
        _get_activity_or_denied(self.request.user, coordination.activity_id)
        return coordination

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('activity-detail', kwargs={'pk': self.object.activity_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = self.object.activity
        return context

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        response = super().form_valid(form)
        _apply_submit_action(self.request, form.instance, 'coordination')
        _log(form.instance.activity, 'coordination', 'update', self.request.user)
        messages.success(self.request, 'تم تحديث نموذج التنسيق والجاهزية بنجاح.')
        return response


class CoordinationDeleteView(ProtectedDeleteMixin, DeleteView):
    model = ActivityCoordination
    template_name = 'activities/coordination_confirm_delete.html'

    def get_object(self, queryset=None):
        coordination = get_object_or_404(ActivityCoordination, pk=self.kwargs['pk'])
        _get_activity_or_denied(self.request.user, coordination.activity_id)
        if not coordination.can_user_edit(self.request.user):
            raise PermissionDenied('غير مسموح لك حذف هذا النموذج.')
        return coordination

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        self.success_url = f'/activities/{obj.activity_id}/'
        if not obj.is_editable():
            messages.error(request, 'لا يمكن حذف نموذج في حالته الحالية.')
            return redirect('activity-detail', pk=obj.activity_id)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        _log(obj.activity, 'coordination', 'delete', request.user)
        messages.success(request, 'تم حذف نموذج التنسيق والجاهزية.')
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def coordination_transition(request, pk, action):
    coordination = get_object_or_404(ActivityCoordination, pk=pk)
    _get_activity_or_denied(request.user, coordination.activity_id)
    _do_transition(request, coordination, 'coordination', action)
    return redirect('activity-detail', pk=coordination.activity_id)


class FinalFinancialCreateView(CreateView):
    model = FinalFinancialAnalysis
    form_class = FinalFinancialAnalysisForm
    template_name = 'activities/final_form.html'

    def dispatch(self, request, *args, **kwargs):
        self.activity = _get_activity_or_denied(request.user, kwargs['activity_pk'])
        coordination = ActivityCoordination.objects.filter(activity=self.activity).first()
        if not coordination or coordination.status != StageStatus.APPROVED:
            messages.error(request, 'التحليل المالي النهائي لا يُتاح إلا بعد اعتماد نموذج التنسيق والجاهزية.')
            return redirect('activity-detail', pk=self.activity.pk)
        if not self.activity.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك دخول هنا')
        if FinalFinancialAnalysis.objects.filter(activity=self.activity).exists():
            messages.error(request, 'يوجد تحليل مالي نهائي مسجل لهذا النشاط بالفعل.')
            return redirect('activity-detail', pk=self.activity.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('activity-detail', kwargs={'pk': self.object.activity_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = self.activity
        return context

    def form_valid(self, form):
        form.instance.activity = self.activity
        form.instance.created_by = self.request.user
        form.instance.last_person = self.request.user
        response = super().form_valid(form)
        _apply_submit_action(self.request, form.instance, 'final')
        _log(self.activity, 'final', 'create', self.request.user)
        messages.success(self.request, 'تم إنشاء التحليل المالي النهائي بنجاح.')
        return response


class FinalFinancialUpdateView(UpdateView):
    model = FinalFinancialAnalysis
    form_class = FinalFinancialAnalysisForm
    template_name = 'activities/final_form.html'
    pk_url_kwarg = 'pk'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj.can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك تعديل هذا التحليل.')
        if not obj.is_editable():
            messages.error(request, 'لا يمكن تعديل نموذج في حالته الحالية.')
            return redirect('activity-detail', pk=obj.activity_id)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        final = get_object_or_404(FinalFinancialAnalysis, pk=self.kwargs['pk'])
        _get_activity_or_denied(self.request.user, final.activity_id)
        return final

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('activity-detail', kwargs={'pk': self.object.activity_id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activity'] = self.object.activity
        return context

    def form_valid(self, form):
        form.instance.last_person = self.request.user
        response = super().form_valid(form)
        _apply_submit_action(self.request, form.instance, 'final')
        _log(form.instance.activity, 'final', 'update', self.request.user)
        messages.success(self.request, 'تم تحديث التحليل المالي النهائي بنجاح.')
        return response


class FinalFinancialDeleteView(ProtectedDeleteMixin, DeleteView):
    model = FinalFinancialAnalysis
    template_name = 'activities/final_confirm_delete.html'

    def get_object(self, queryset=None):
        final = get_object_or_404(FinalFinancialAnalysis, pk=self.kwargs['pk'])
        _get_activity_or_denied(self.request.user, final.activity_id)
        if not final.can_user_edit(self.request.user):
            raise PermissionDenied('غير مسموح لك حذف هذا التحليل.')
        return final

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        self.success_url = f'/activities/{obj.activity_id}/'
        if not obj.is_editable():
            messages.error(request, 'لا يمكن حذف نموذج في حالته الحالية.')
            return redirect('activity-detail', pk=obj.activity_id)
        return super().dispatch(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        _log(obj.activity, 'final', 'delete', request.user)
        messages.success(request, 'تم حذف التحليل المالي النهائي.')
        return super().delete(request, *args, **kwargs)


@login_required
@require_POST
def final_transition(request, pk, action):
    final = get_object_or_404(FinalFinancialAnalysis, pk=pk)
    _get_activity_or_denied(request.user, final.activity_id)
    _do_transition(request, final, 'final', action)
    return redirect('activity-detail', pk=final.activity_id)


def _pdf_response(buffer, filename):
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def activity_pdf(request, pk):
    activity = _get_activity_or_denied(request.user, pk)
    buffer = build_activity_pdf(activity)
    return _pdf_response(buffer, f'activity-contract-{activity.form_number or activity.pk}.pdf')


@login_required
def financial_pdf(request, pk):
    analysis = get_object_or_404(FinancialAnalysis, pk=pk)
    _get_activity_or_denied(request.user, analysis.activity_id)
    buffer = build_financial_pdf(analysis)
    return _pdf_response(buffer, f'activity-financial-{analysis.form_number or analysis.pk}.pdf')


@login_required
def coordination_pdf(request, pk):
    coordination = get_object_or_404(ActivityCoordination, pk=pk)
    _get_activity_or_denied(request.user, coordination.activity_id)
    buffer = build_coordination_pdf(coordination)
    return _pdf_response(buffer, f'activity-coordination-{coordination.form_number or coordination.pk}.pdf')


@login_required
def final_pdf(request, pk):
    final = get_object_or_404(FinalFinancialAnalysis, pk=pk)
    _get_activity_or_denied(request.user, final.activity_id)
    buffer = build_final_pdf(final)
    return _pdf_response(buffer, f'activity-final-financial-{final.form_number or final.pk}.pdf')
