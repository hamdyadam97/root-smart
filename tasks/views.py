from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.mixins import ProtectedDeleteMixin
from accounts.models import Person
from . import services
from .forms import TaskCommentForm, TaskForm
from .models import (
    AssignmentStatus, DeductionReason, DeductionStatus, Task, TaskAssignment, TaskDeduction,
    TaskFrequency, TaskPriority, TaskStatus,
)


def _get_task_or_denied(user, pk):
    task = get_object_or_404(Task.objects.select_related('branch', 'created_by'), pk=pk)
    if not task.can_user_view(user):
        raise PermissionDenied('غير مسموح لك دخول هنا')
    return task


def _branch_ids(user, perm):
    return [b.pk for b in user.get_branches_for_perm(perm)]


def _can_manage_deductions(user, branch=None):
    if user.is_executive():
        return True
    if branch is None:
        return user.has_perm_on_any_branch('approve_task')
    return user.has_perm('approve_task', branch=branch)


# ============================================================
# المهام
# ============================================================

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 25

    def get_scope(self):
        scope = self.request.GET.get('scope', 'mine')
        return scope if scope in ('mine', 'created', 'all') else 'mine'

    def get_queryset(self):
        user = self.request.user
        qs = Task.objects.select_related('branch', 'created_by').annotate(
            assignee_count=Count('assignments', distinct=True),
            closed_count=Count('assignments', filter=Q(assignments__status=AssignmentStatus.CLOSED), distinct=True),
        )
        scope = self.get_scope()
        if scope == 'mine':
            qs = qs.filter(assignments__person=user)
        elif scope == 'created':
            qs = qs.filter(created_by=user)
        elif not user.is_executive():
            qs = qs.filter(Q(branch__in=_branch_ids(user, 'view_task')) | Q(created_by=user))

        params = self.request.GET
        search = params.get('search', '').strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        if params.get('status'):
            qs = qs.filter(status=params['status'])
        if params.get('frequency'):
            qs = qs.filter(frequency=params['frequency'])
        if params.get('priority'):
            qs = qs.filter(priority=params['priority'])
        if params.get('overdue') == '1':
            qs = qs.filter(status=TaskStatus.OPEN, due_date__lt=timezone.localdate())
        return qs.distinct().order_by('status', 'due_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['scope'] = self.get_scope()
        context['can_view_all'] = user.is_executive() or user.has_perm_on_any_branch('view_task')
        context['can_add'] = user.is_executive() or user.has_perm_on_any_branch('add_task')
        context['status_choices'] = TaskStatus.choices
        context['frequency_choices'] = TaskFrequency.choices
        context['priority_choices'] = TaskPriority.choices
        context['today'] = timezone.localdate()
        my = TaskAssignment.objects.filter(person=user, task__status=TaskStatus.OPEN)
        context['my_open_count'] = my.exclude(status=AssignmentStatus.CLOSED).count()
        context['my_overdue_count'] = my.exclude(status=AssignmentStatus.CLOSED).filter(
            task__due_date__lt=timezone.localdate()).count()
        context['pending_close_count'] = TaskAssignment.objects.filter(
            task__created_by=user, status=AssignmentStatus.CLOSE_REQUESTED,
        ).values('task').distinct().count()
        context['my_deductions_month'] = TaskDeduction.objects.filter(
            person=user, status=DeductionStatus.ACTIVE,
            period_start__year=context['today'].year, period_start__month=context['today'].month,
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return context


class _TaskFormMixin:
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def _sync_assignees(self, task, persons):
        current = {a.person_id: a for a in task.assignments.all()}
        wanted = {p.pk: p for p in persons}
        task.assignments.filter(person_id__in=set(current) - set(wanted)).delete()
        added = [wanted[pk] for pk in set(wanted) - set(current)]
        TaskAssignment.objects.bulk_create([TaskAssignment(task=task, person=p) for p in added])
        return added


class TaskCreateView(LoginRequiredMixin, _TaskFormMixin, CreateView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not (
            request.user.is_executive() or request.user.has_perm_on_any_branch('add_task')
        ):
            raise PermissionDenied('غير مسموح لك إنشاء مهام.')
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        task = form.save(commit=False)
        task.created_by = self.request.user
        task.save()
        added = self._sync_assignees(task, form.cleaned_data['assignees'])
        services.on_assigned(task, added, self.request.user)
        messages.success(self.request, 'تم إنشاء المهمة وإشعار الموظفين المكلفين.')
        return redirect('task-detail', pk=task.pk)


class TaskUpdateView(LoginRequiredMixin, _TaskFormMixin, UpdateView):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not self.get_object().can_user_edit(request.user):
            raise PermissionDenied('غير مسموح لك تعديل هذه المهمة.')
        return super().dispatch(request, *args, **kwargs)

    @transaction.atomic
    def form_valid(self, form):
        task = form.save()
        added = self._sync_assignees(task, form.cleaned_data['assignees'])
        services.on_assigned(task, added, self.request.user)
        task.refresh_status()
        messages.success(self.request, 'تم تحديث المهمة.')
        return redirect('task-detail', pk=task.pk)


class TaskDeleteView(LoginRequiredMixin, ProtectedDeleteMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')
    context_object_name = 'task'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not self.get_object().can_user_delete(request.user):
            raise PermissionDenied('غير مسموح لك حذف هذه المهمة.')
        return super().dispatch(request, *args, **kwargs)


@login_required
def task_detail(request, pk):
    task = _get_task_or_denied(request.user, pk)
    user = request.user
    assignments = list(task.assignments.select_related('person', 'closed_by'))
    my_assignment = next((a for a in assignments if a.person_id == user.pk), None)
    can_approve = task.can_user_approve(user)

    form = TaskCommentForm()
    if request.method == 'POST':
        if not (my_assignment or can_approve or task.created_by_id == user.pk):
            raise PermissionDenied('غير مسموح لك التعليق على هذه المهمة.')
        if task.status == TaskStatus.CANCELLED:
            messages.error(request, 'لا يمكن التعليق على مهمة ملغاة.')
            return redirect('task-detail', pk=task.pk)
        form = TaskCommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = user
            comment.save()
            services.on_comment(task, comment)
            messages.success(request, 'تم إضافة التعليق.')
            return redirect(f'{request.path}#comments')

    today = timezone.localdate()
    commented_today = {
        a.person_id for a in assignments
        if task.comments.filter(author_id=a.person_id, created_at__date=today).exists()
    }
    deductions = task.deductions.select_related('person', 'waived_by')
    if not (can_approve or task.created_by_id == user.pk):
        deductions = deductions.filter(person=user)

    return render(request, 'tasks/task_detail.html', {
        'task': task,
        'assignments': assignments,
        'my_assignment': my_assignment,
        'comments': task.comments.select_related('author'),
        'form': form,
        'can_edit': task.can_user_edit(user),
        'can_delete': task.can_user_delete(user),
        'can_approve': can_approve,
        'can_manage_deductions': _can_manage_deductions(user, task.branch),
        'commented_today': commented_today,
        'deductions': deductions,
        'today': today,
    })


@login_required
@require_POST
def task_transition(request, pk, action):
    task = _get_task_or_denied(request.user, pk)
    user = request.user
    assignment = None
    if request.POST.get('assignment'):
        assignment = get_object_or_404(TaskAssignment, pk=request.POST['assignment'], task=task)

    if action == 'request_close':
        assignment = assignment or task.assignments.filter(person=user).first()
        if not assignment or assignment.person_id != user.pk:
            raise PermissionDenied('طلب الإغلاق متاح للموظف المكلف فقط.')
        if task.status != TaskStatus.OPEN or assignment.status != AssignmentStatus.OPEN:
            messages.error(request, 'لا يمكن طلب إغلاق المهمة في حالتها الحالية.')
        else:
            services.request_close(assignment, user, request.POST.get('note', '').strip())
            messages.success(request, 'تم إرسال طلب الإغلاق لمنشئ المهمة.')

    elif action in ('approve_close', 'reject_close'):
        if not task.can_user_approve(user):
            raise PermissionDenied('غير مسموح لك اعتماد إغلاق هذه المهمة.')
        if not assignment:
            messages.error(request, 'حدد الموظف.')
        elif action == 'approve_close':
            if assignment.status == AssignmentStatus.CLOSED:
                messages.error(request, 'المهمة منتهية بالفعل لهذا الموظف.')
            else:
                services.approve_close(assignment, user)
                messages.success(request, 'تم اعتماد إغلاق المهمة.')
        else:
            reason = request.POST.get('reason', '').strip()
            if assignment.status != AssignmentStatus.CLOSE_REQUESTED:
                messages.error(request, 'لا يوجد طلب إغلاق لرفضه.')
            elif not reason:
                messages.error(request, 'يجب إدخال سبب الرفض.')
            else:
                services.reject_close(assignment, user, reason)
                messages.success(request, 'تم رفض طلب الإغلاق وإعادة المهمة للموظف.')

    elif action == 'cancel':
        if not task.can_user_edit(user):
            raise PermissionDenied('غير مسموح لك إلغاء هذه المهمة.')
        if task.status != TaskStatus.OPEN:
            messages.error(request, 'المهمة ليست مفتوحة.')
        else:
            services.cancel_task(task, user)
            messages.success(request, 'تم إلغاء المهمة.')

    elif action == 'reopen':
        if not task.can_user_edit(user):
            raise PermissionDenied('غير مسموح لك إعادة فتح هذه المهمة.')
        if task.status == TaskStatus.OPEN:
            messages.error(request, 'المهمة مفتوحة بالفعل.')
        else:
            services.reopen_task(task, user)
            messages.success(request, 'تمت إعادة فتح المهمة.')
    else:
        raise PermissionDenied('إجراء غير معروف')

    return redirect('task-detail', pk=task.pk)


# ============================================================
# الخصومات
# ============================================================

@login_required
def deduction_list(request):
    user = request.user
    qs = TaskDeduction.objects.select_related('task', 'task__branch', 'person', 'waived_by')
    can_manage = _can_manage_deductions(user)
    if user.is_executive():
        pass
    elif can_manage:
        qs = qs.filter(Q(task__branch__in=_branch_ids(user, 'approve_task')) | Q(person=user))
    else:
        qs = qs.filter(person=user)

    today = timezone.localdate()
    month = request.GET.get('month') or today.strftime('%Y-%m')
    try:
        year, mon = (int(x) for x in month.split('-'))
        qs = qs.filter(period_start__year=year, period_start__month=mon)
    except ValueError:
        month = ''
    if request.GET.get('person') and can_manage:
        qs = qs.filter(person_id=request.GET['person'])
    if request.GET.get('reason'):
        qs = qs.filter(reason=request.GET['reason'])
    status = request.GET.get('status', DeductionStatus.ACTIVE)
    if status:
        qs = qs.filter(status=status)
    qs = qs.distinct()

    summary = (
        TaskDeduction.objects.filter(pk__in=qs.values('pk'))
        .values('person_id', 'person__first_name', 'person__second_name', 'person__forth_name')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
    )
    persons = Person.objects.filter(pk__in=qs.values('person_id')) if can_manage else []

    return render(request, 'tasks/deduction_list.html', {
        'deductions': qs.order_by('-period_start', 'person__first_name'),
        'summary': summary,
        'total': qs.aggregate(t=Sum('amount'))['t'] or Decimal('0.00'),
        'can_manage': can_manage,
        'month': month,
        'persons': persons,
        'reason_choices': DeductionReason.choices,
        'status_choices': DeductionStatus.choices,
        'status': status,
    })


@login_required
@require_POST
def deduction_waive(request, pk):
    deduction = get_object_or_404(TaskDeduction.objects.select_related('task'), pk=pk)
    if not _can_manage_deductions(request.user, deduction.task.branch):
        raise PermissionDenied('غير مسموح لك إلغاء الخصومات.')
    if request.POST.get('restore'):
        deduction.status = DeductionStatus.ACTIVE
        deduction.waive_reason = ''
        deduction.waived_by = None
        deduction.waived_at = None
        messages.success(request, 'تمت إعادة تفعيل الخصم.')
    else:
        deduction.status = DeductionStatus.WAIVED
        deduction.waive_reason = request.POST.get('reason', '').strip()
        deduction.waived_by = request.user
        deduction.waived_at = timezone.now()
        messages.success(request, 'تم إلغاء الخصم.')
    deduction.save()
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect('deduction-list')


@login_required
@require_POST
def deductions_process(request):
    if not _can_manage_deductions(request.user):
        raise PermissionDenied('غير مسموح لك دخول هنا')
    created = services.process_penalties()
    messages.success(request, f'تم احتساب الخصومات حتى أمس: {len(created)} خصم جديد.')
    return redirect('deduction-list')
