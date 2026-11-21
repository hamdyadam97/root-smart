"""منطق المهام: انتقالات الإغلاق، الإشعارات، واحتساب الخصومات اليومية."""
from collections import defaultdict
from datetime import timedelta

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from notifications.models import AppNotification

from .models import (
    AssignmentStatus, DeductionReason, Task, TaskDeduction, TaskFrequency, TaskStatus,
)

# الجمعة عطلة: لا يُطلب فيها تعليق يومي ولا يُحتسب فيها يوم تأخير.
WEEKEND_DAYS = {4}
# الأسبوع يبدأ يوم السبت (weekday() == 5).
WEEK_START_DAY = 5


def notify(users, title, body, task):
    url = reverse('task-detail', args=[task.pk])
    seen = set()
    rows = []
    for user in users:
        if user is None or user.pk in seen:
            continue
        seen.add(user.pk)
        rows.append(AppNotification(
            user=user, title=title, body=body, notification_type='تنبيه', action_url=url,
        ))
    AppNotification.objects.bulk_create(rows)


def _name(user):
    return ' '.join(user.get_full_name().split()) or user.email


def _scope(assignment):
    """المهمة المشتركة تُغلق لكل المكلفين معًا، والفردية لكل موظف وحده."""
    if assignment.task.is_shared:
        return list(assignment.task.assignments.select_related('person'))
    return [assignment]


@transaction.atomic
def request_close(assignment, user, note=''):
    now = timezone.now()
    for a in _scope(assignment):
        a.status = AssignmentStatus.CLOSE_REQUESTED
        a.close_requested_at = now
        a.close_note = note
        a.rejection_reason = ''
        a.save()
    task = assignment.task
    notify([task.created_by], 'طلب إغلاق مهمة',
           f'{_name(user)} طلب إغلاق المهمة «{task.title}».', task)


@transaction.atomic
def approve_close(assignment, user):
    now = timezone.now()
    targets = _scope(assignment)
    for a in targets:
        a.status = AssignmentStatus.CLOSED
        a.closed_at = now
        a.closed_by = user
        if not a.close_requested_at:
            a.close_requested_at = now
        a.save()
    task = assignment.task
    task.refresh_status()
    notify([a.person for a in targets], 'تم اعتماد إغلاق المهمة',
           f'اعتمد {_name(user)} إغلاق المهمة «{task.title}».', task)


@transaction.atomic
def reject_close(assignment, user, reason):
    targets = _scope(assignment)
    for a in targets:
        a.status = AssignmentStatus.OPEN
        a.close_requested_at = None
        a.rejection_reason = reason
        a.save()
    task = assignment.task
    notify([a.person for a in targets], 'تم رفض إغلاق المهمة',
           f'رفض {_name(user)} إغلاق المهمة «{task.title}»: {reason}', task)


@transaction.atomic
def cancel_task(task, user):
    task.status = TaskStatus.CANCELLED
    task.cancelled_at = timezone.now()
    task.save()
    notify([a.person for a in task.assignments.select_related('person')], 'تم إلغاء مهمة',
           f'ألغى {_name(user)} المهمة «{task.title}».', task)


@transaction.atomic
def reopen_task(task, user):
    task.status = TaskStatus.OPEN
    task.cancelled_at = None
    task.closed_at = None
    task.save()
    task.assignments.update(
        status=AssignmentStatus.OPEN, close_requested_at=None, closed_at=None, closed_by=None,
    )
    notify([a.person for a in task.assignments.select_related('person')], 'تمت إعادة فتح مهمة',
           f'أعاد {_name(user)} فتح المهمة «{task.title}».', task)


def on_comment(task, comment):
    """إشعار منشئ المهمة بتعليق الموظف، وإشعار المكلفين بتعليق المنشئ أو المدير."""
    author = comment.author
    assignee_ids = set(task.assignments.values_list('person_id', flat=True))
    if author.pk in assignee_ids:
        recipients = [task.created_by] if task.created_by_id != author.pk else []
    else:
        recipients = [a.person for a in task.assignments.select_related('person')]
    preview = comment.body if len(comment.body) <= 120 else comment.body[:117] + '...'
    notify(recipients, 'تعليق جديد على مهمة', f'{_name(author)} علّق على «{task.title}»: {preview}', task)


def on_assigned(task, persons, user):
    notify(persons, 'مهمة جديدة مسندة إليك',
           f'أسند إليك {_name(user)} المهمة «{task.title}».', task)


# ============================================================
# احتساب الخصومات — يُشغَّل يوميًا (python manage.py process_task_penalties)
# ============================================================

def _local_date(dt):
    return timezone.localtime(dt).date()


def _days(start, end):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _work_days(start, end):
    return [d for d in _days(start, end) if d.weekday() not in WEEKEND_DAYS]


def _hard_stop(task, assignment):
    """آخر يوم كان الموظف مطالبًا فيه بالعمل على المهمة (None = مستمرة)."""
    stops = []
    if assignment.close_requested_at:
        stops.append(_local_date(assignment.close_requested_at) - timedelta(days=1))
    if task.cancelled_at:
        stops.append(_local_date(task.cancelled_at) - timedelta(days=1))
    return min(stops) if stops else None


def _assignment_deductions(task, assignment, yesterday, comment_days):
    """قائمة (السبب، بداية الفترة، عدد المخالفات، المبلغ) المستحقة للإسناد حتى أمس."""
    out = []
    stop = _hard_stop(task, assignment)
    horizon = min(stop, yesterday) if stop else yesterday

    if task.due_date and task.late_penalty_amount > 0:
        for d in _work_days(task.due_date + timedelta(days=1), horizon):
            out.append((DeductionReason.LATE, d, 1, task.late_penalty_amount))

    amount = task.missed_comment_penalty_amount
    if amount <= 0 or task.frequency == TaskFrequency.ONCE:
        return out

    start = max(task.start_date, _local_date(assignment.assigned_at))
    comment_stop = min(x for x in (stop, task.due_date) if x) if (stop or task.due_date) else None

    if task.frequency == TaskFrequency.DAILY:
        end = min(comment_stop, yesterday) if comment_stop else yesterday
        for d in _work_days(start, end):
            if d not in comment_days:
                out.append((DeductionReason.MISSED_COMMENT, d, 1, amount))
        return out

    # أسبوعية: يُقيَّم كل أسبوع بعد انتهائه (أو بعد توقف المهمة داخله).
    week_start = start - timedelta(days=(start.weekday() - WEEK_START_DAY) % 7)
    while week_start <= yesterday:
        week_end = week_start + timedelta(days=6)
        window_start = max(week_start, start)
        window_end = min(week_end, comment_stop) if comment_stop else week_end
        if window_end > yesterday:
            break
        if window_start <= window_end:
            work_days = _work_days(window_start, window_end)
            required = min(task.weekly_comment_count, len(work_days))
            done = sum(1 for d in _days(window_start, window_end) if d in comment_days)
            missing = required - done
            if missing > 0:
                out.append((DeductionReason.MISSED_COMMENT, week_start, missing, amount * missing))
        if comment_stop and week_end >= comment_stop:
            break
        week_start += timedelta(days=7)
    return out


def process_penalties(today=None):
    """ينشئ الخصومات المستحقة حتى أمس. آمن للتشغيل أكثر من مرة: لا يكرر خصمًا لنفس الفترة."""
    today = today or timezone.localdate()
    yesterday = today - timedelta(days=1)
    recent = timezone.now() - timedelta(days=30)

    tasks = (
        Task.objects.filter(status=TaskStatus.OPEN)
        | Task.objects.filter(closed_at__gte=recent)
        | Task.objects.filter(cancelled_at__gte=recent)
    ).distinct().select_related('created_by')

    created = []
    for task in tasks:
        if task.late_penalty_amount <= 0 and task.missed_comment_penalty_amount <= 0:
            continue
        comments = defaultdict(set)
        for author_id, created_at in task.comments.values_list('author_id', 'created_at'):
            comments[author_id].add(_local_date(created_at))

        for assignment in task.assignments.select_related('person'):
            for reason, period, count, amount in _assignment_deductions(
                task, assignment, yesterday, comments[assignment.person_id]
            ):
                deduction, was_created = TaskDeduction.objects.get_or_create(
                    task=task, person=assignment.person, reason=reason, period_start=period,
                    defaults={'missing_count': count, 'amount': amount},
                )
                if was_created:
                    created.append(deduction)

    _notify_deductions(created)
    return created


def _notify_deductions(deductions):
    by_person = defaultdict(list)
    by_creator = defaultdict(list)
    for d in deductions:
        by_person[(d.person, d.task)].append(d)
        if d.task.created_by_id and d.task.created_by_id != d.person_id:
            by_creator[(d.task.created_by, d.task)].append(d)

    for (person, task), items in by_person.items():
        total = sum(d.amount for d in items)
        notify([person], 'خصم على مهمة',
               f'تم تسجيل {len(items)} خصم بإجمالي {total} دينار على المهمة «{task.title}».', task)
    for (creator, task), items in by_creator.items():
        names = '، '.join(sorted({_name(d.person) for d in items}))
        total = sum(d.amount for d in items)
        notify([creator], 'خصومات على مهمة أنشأتها',
               f'تم تسجيل خصومات بإجمالي {total} دينار على المهمة «{task.title}» ({names}).', task)
