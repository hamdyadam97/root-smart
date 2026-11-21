from datetime import date, datetime
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import EmployeeRole, Permission, Person, Role
from core.models import Branch, Company
from notifications.models import AppNotification
from . import services
from .models import (
    AssignmentStatus, DeductionReason, Task, TaskAssignment, TaskComment, TaskDeduction,
    TaskFrequency, TaskMode, TaskStatus,
)

TASK_PERMS = ['view_task', 'add_task', 'change_task', 'delete_task', 'approve_task']


def _aware(y, m, d, h=10):
    return timezone.make_aware(datetime(y, m, d, h, 0))


def _grant_role(user, branch, codenames, role_name):
    role = Role.objects.create(name=role_name)
    for codename in codenames:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={'name': codename, 'app_label': 'tasks', 'model_name': 'task', 'action': codename.split('_', 1)[0]},
        )
        role.permissions.add(perm)
    EmployeeRole.objects.create(person=user, role=role, branch=branch)


class TaskTestBase(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Root Academy')
        self.branch = Branch.objects.create(company=self.company, code=1, name='Main Branch')
        self.manager = Person.objects.create_user(
            email='manager@example.com', password='pass12345', first_name='Man', forth_name='Ager',
            branch=self.branch,
        )
        self.emp1 = Person.objects.create_user(
            email='emp1@example.com', password='pass12345', first_name='Emp', forth_name='One',
            branch=self.branch,
        )
        self.emp2 = Person.objects.create_user(
            email='emp2@example.com', password='pass12345', first_name='Emp', forth_name='Two',
            branch=self.branch,
        )
        self.stranger = Person.objects.create_user(
            email='stranger@example.com', password='pass12345', first_name='Str', forth_name='Anger',
        )
        _grant_role(self.manager, self.branch, TASK_PERMS, 'task_manager')

    def make_task(self, assignees, assigned_on=date(2026, 11, 1), **fields):
        defaults = {
            'title': 'متابعة العملاء', 'branch': self.branch, 'created_by': self.manager,
            'start_date': date(2026, 11, 1),
        }
        defaults.update(fields)
        task = Task.objects.create(**defaults)
        for person in assignees:
            TaskAssignment.objects.create(task=task, person=person)
        task.assignments.update(assigned_at=_aware(assigned_on.year, assigned_on.month, assigned_on.day, 8))
        return task

    def comment(self, task, author, day):
        c = TaskComment.objects.create(task=task, author=author, body='تحديث')
        TaskComment.objects.filter(pk=c.pk).update(created_at=_aware(2026, 11, day))


class PenaltyTests(TaskTestBase):
    def test_week_layout_assumption(self):
        self.assertEqual(date(2026, 11, 14).weekday(), 5)  # السبت
        self.assertEqual(date(2026, 11, 13).weekday(), 4)  # الجمعة

    def test_daily_missing_comments_skip_friday_and_are_idempotent(self):
        task = self.make_task(
            [self.emp1], start_date=date(2026, 11, 12), frequency=TaskFrequency.DAILY,
            missed_comment_penalty_amount=Decimal('2.00'),
        )
        self.comment(task, self.emp1, 12)
        self.comment(task, self.emp1, 15)
        # الأيام حتى أمس (17): 12 ✓، 13 جمعة، 14 ✗، 15 ✓، 16 ✗، 17 ✗
        created = services.process_penalties(today=date(2026, 11, 18))
        self.assertEqual(
            sorted(d.period_start.day for d in created), [14, 16, 17]
        )
        self.assertTrue(all(d.amount == Decimal('2.00') for d in created))
        self.assertEqual(services.process_penalties(today=date(2026, 11, 18)), [])

    def test_late_penalty_per_work_day_until_close_request(self):
        task = self.make_task(
            [self.emp1], due_date=date(2026, 11, 16), late_penalty_amount=Decimal('5.00'),
        )
        created = services.process_penalties(today=date(2026, 11, 19))
        self.assertEqual(sorted(d.period_start.day for d in created), [17, 18])

        TaskAssignment.objects.filter(task=task).update(
            status=AssignmentStatus.CLOSE_REQUESTED, close_requested_at=_aware(2026, 11, 19),
        )
        self.assertEqual(services.process_penalties(today=date(2026, 11, 25)), [])

    def test_weekly_counts_distinct_days_after_week_ends(self):
        task = self.make_task(
            [self.emp1], start_date=date(2026, 11, 7), frequency=TaskFrequency.WEEKLY,
            weekly_comment_count=3, missed_comment_penalty_amount=Decimal('4.00'),
        )
        self.comment(task, self.emp1, 8)
        self.comment(task, self.emp1, 8)
        self.comment(task, self.emp1, 10)
        # الأسبوع الحالي (14–20) لم ينته بعد، فلا يُقيَّم.
        created = services.process_penalties(today=date(2026, 11, 16))
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0].period_start, date(2026, 11, 7))
        self.assertEqual(created[0].missing_count, 1)
        self.assertEqual(created[0].amount, Decimal('4.00'))

    def test_each_assignee_is_judged_separately_and_notified(self):
        task = self.make_task(
            [self.emp1, self.emp2], start_date=date(2026, 11, 16), frequency=TaskFrequency.DAILY,
            missed_comment_penalty_amount=Decimal('1.00'),
        )
        self.comment(task, self.emp1, 16)
        created = services.process_penalties(today=date(2026, 11, 17))
        self.assertEqual([d.person for d in created], [self.emp2])
        self.assertTrue(AppNotification.objects.filter(user=self.emp2, title='خصم على مهمة').exists())
        self.assertTrue(AppNotification.objects.filter(user=self.manager, title='خصومات على مهمة أنشأتها').exists())

    def test_zero_amounts_create_nothing(self):
        self.make_task([self.emp1], due_date=date(2026, 11, 2), frequency=TaskFrequency.DAILY)
        self.assertEqual(services.process_penalties(today=date(2026, 11, 20)), [])


class CloseFlowTests(TaskTestBase):
    def test_shared_task_closes_for_everyone(self):
        task = self.make_task([self.emp1, self.emp2], due_date=date(2026, 12, 1), mode=TaskMode.SHARED)
        a1 = task.assignments.get(person=self.emp1)
        services.request_close(a1, self.emp1, 'خلصت')
        self.assertEqual(
            set(task.assignments.values_list('status', flat=True)), {AssignmentStatus.CLOSE_REQUESTED}
        )
        self.assertTrue(AppNotification.objects.filter(user=self.manager, title='طلب إغلاق مهمة').exists())
        services.approve_close(a1, self.manager)
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.CLOSED)

    def test_individual_task_closes_per_person(self):
        task = self.make_task([self.emp1, self.emp2], due_date=date(2026, 12, 1), mode=TaskMode.INDIVIDUAL)
        a1 = task.assignments.get(person=self.emp1)
        services.request_close(a1, self.emp1)
        services.approve_close(a1, self.manager)
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.OPEN)
        self.assertEqual(task.assignments.get(person=self.emp2).status, AssignmentStatus.OPEN)

    def test_reject_returns_task_to_employee(self):
        task = self.make_task([self.emp1], due_date=date(2026, 12, 1))
        a1 = task.assignments.get()
        services.request_close(a1, self.emp1)
        services.reject_close(a1, self.manager, 'ناقص التقرير')
        a1.refresh_from_db()
        self.assertEqual(a1.status, AssignmentStatus.OPEN)
        self.assertIsNone(a1.close_requested_at)
        self.assertTrue(AppNotification.objects.filter(user=self.emp1, title='تم رفض إغلاق المهمة').exists())


class TaskViewTests(TaskTestBase):
    def client_for(self, user):
        c = Client()
        c.force_login(user)
        return c

    def test_create_task_assigns_and_notifies(self):
        resp = self.client_for(self.manager).post(reverse('task-create'), {
            'title': 'تقرير المبيعات', 'description': '', 'branch': self.branch.pk,
            'priority': 'normal', 'mode': 'individual', 'frequency': 'weekly',
            'start_date': '2026-11-21', 'due_date': '', 'weekly_comment_count': 2,
            'late_penalty_amount': '0', 'missed_comment_penalty_amount': '3',
            'assignees': [self.emp1.pk, self.emp2.pk],
        })
        task = Task.objects.get(title='تقرير المبيعات')
        self.assertRedirects(resp, reverse('task-detail', args=[task.pk]))
        self.assertEqual(task.assignments.count(), 2)
        self.assertEqual(AppNotification.objects.filter(title='مهمة جديدة مسندة إليك').count(), 2)

    def test_once_task_requires_due_date(self):
        resp = self.client_for(self.manager).post(reverse('task-create'), {
            'title': 'x', 'branch': self.branch.pk, 'priority': 'normal', 'mode': 'individual',
            'frequency': 'once', 'start_date': '2026-11-21', 'weekly_comment_count': 1,
            'late_penalty_amount': '0', 'missed_comment_penalty_amount': '0',
            'assignees': [self.emp1.pk],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Task.objects.exists())

    def test_employee_without_permission_cannot_create(self):
        self.assertEqual(self.client_for(self.emp1).get(reverse('task-create')).status_code, 403)

    def test_visibility(self):
        task = self.make_task([self.emp1], due_date=date(2026, 12, 1))
        url = reverse('task-detail', args=[task.pk])
        self.assertEqual(self.client_for(self.emp1).get(url).status_code, 200)
        self.assertEqual(self.client_for(self.manager).get(url).status_code, 200)
        self.assertEqual(self.client_for(self.stranger).get(url).status_code, 403)
        self.assertEqual(self.client_for(self.emp2).get(url).status_code, 403)

    def test_assignee_comment_notifies_creator(self):
        task = self.make_task([self.emp1], due_date=date(2026, 12, 1))
        self.client_for(self.emp1).post(reverse('task-detail', args=[task.pk]), {'body': 'تم التواصل مع 5 عملاء'})
        self.assertEqual(task.comments.count(), 1)
        self.assertTrue(AppNotification.objects.filter(user=self.manager, title='تعليق جديد على مهمة').exists())

    def test_only_assignee_can_request_close_and_only_approver_can_approve(self):
        task = self.make_task([self.emp1], due_date=date(2026, 12, 1))
        a1 = task.assignments.get()
        url = reverse('task-transition', args=[task.pk, 'request_close'])
        self.assertEqual(self.client_for(self.emp2).post(url, {'assignment': a1.pk}).status_code, 403)
        self.client_for(self.emp1).post(url, {'assignment': a1.pk})
        approve = reverse('task-transition', args=[task.pk, 'approve_close'])
        self.assertEqual(self.client_for(self.emp1).post(approve, {'assignment': a1.pk}).status_code, 403)
        self.client_for(self.manager).post(approve, {'assignment': a1.pk})
        task.refresh_from_db()
        self.assertEqual(task.status, TaskStatus.CLOSED)

    def test_employee_sees_only_own_deductions_and_cannot_waive(self):
        task = self.make_task([self.emp1, self.emp2], due_date=date(2026, 12, 1))
        d1 = TaskDeduction.objects.create(task=task, person=self.emp1, reason=DeductionReason.LATE,
                                          period_start=date(2026, 11, 3), amount=Decimal('5'))
        TaskDeduction.objects.create(task=task, person=self.emp2, reason=DeductionReason.LATE,
                                     period_start=date(2026, 11, 3), amount=Decimal('7'))
        resp = self.client_for(self.emp1).get(reverse('deduction-list'), {'month': '2026-11'})
        self.assertEqual(list(resp.context['deductions']), [d1])
        self.assertEqual(
            self.client_for(self.emp1).post(reverse('deduction-waive', args=[d1.pk])).status_code, 403
        )
        self.client_for(self.manager).post(reverse('deduction-waive', args=[d1.pk]), {'reason': 'عذر طبي'})
        d1.refresh_from_db()
        self.assertEqual(d1.status, 'waived')

    def test_pages_render(self):
        task = self.make_task([self.emp1], due_date=date(2026, 11, 2), mode=TaskMode.SHARED)
        manager = self.client_for(self.manager)
        for scope in ('mine', 'created', 'all'):
            resp = manager.get(reverse('task-list'), {'scope': scope})
            self.assertEqual(resp.status_code, 200)
        self.assertContains(manager.get(reverse('task-list'), {'scope': 'created'}), task.title)
        self.assertContains(self.client_for(self.emp1).get(reverse('task-list')), task.title)
        self.assertEqual(manager.get(reverse('task-create')).status_code, 200)
        self.assertEqual(manager.get(reverse('task-update', args=[task.pk])).status_code, 200)
        self.assertEqual(manager.get(reverse('task-delete', args=[task.pk])).status_code, 200)
        self.assertEqual(manager.get(reverse('deduction-list')).status_code, 200)
        self.assertEqual(manager.post(reverse('deductions-process')).status_code, 302)

    def test_task_form_in_modal_via_ajax(self):
        manager = self.client_for(self.manager)
        ajax = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}
        resp = manager.get(reverse('task-create'), **ajax)
        self.assertContains(resp, 'class="task-form"')
        self.assertNotContains(resp, '<html')
        data = {
            'title': 'مهمة مودال', 'branch': self.branch.pk, 'priority': 'normal', 'mode': 'shared',
            'frequency': 'once', 'start_date': '2026-11-21', 'weekly_comment_count': 1,
            'late_penalty_amount': '0', 'missed_comment_penalty_amount': '0', 'assignees': [self.emp1.pk],
        }
        # خطأ تحقق: يرجع النموذج بالأخطاء داخل المودال
        resp = manager.post(reverse('task-create'), data, **ajax)
        self.assertContains(resp, 'class="task-form"')
        self.assertFalse(Task.objects.exists())
        resp = manager.post(reverse('task-create'), {**data, 'due_date': '2026-11-30'}, **ajax)
        task = Task.objects.get(title='مهمة مودال')
        self.assertEqual(resp.json(), {'redirect': reverse('task-detail', args=[task.pk])})

    def test_detail_page_has_action_modals(self):
        task = self.make_task([self.emp1], due_date=date(2026, 12, 1))
        url = reverse('task-detail', args=[task.pk])
        page = self.client_for(self.manager).get(url)
        for modal_id in ('commentModal', 'cancelModal', 'deleteModal', 'approveCloseModal', 'taskFormModal'):
            self.assertContains(page, f'id="{modal_id}"')
        self.assertContains(self.client_for(self.emp1).get(url), 'id="requestCloseModal"')
        # تعليق فارغ يعيد الصفحة ويفتح مودال التعليق تلقائيًا
        resp = self.client_for(self.emp1).post(url, {'body': ''})
        self.assertContains(resp, "getElementById('commentModal')).show()")

    def test_my_notifications_page_needs_no_permission(self):
        AppNotification.objects.create(user=self.emp1, title='t', body='b', notification_type='تنبيه')
        resp = self.client_for(self.emp1).get(reverse('my-notifications'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['unread_notifications_count'], 1)
