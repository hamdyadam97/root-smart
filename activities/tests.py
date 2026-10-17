from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import EmployeeRole, Permission, Person, Role
from core.models import Branch, Company
from .models import (
    Activity, ActivityCoordination, ActivityLog, FinancialAnalysis, FinalFinancialAnalysis, StageStatus,
)


ACTIVITY_PERMS = [
    'view_activity', 'add_activity', 'change_activity', 'delete_activity',
    'view_financialanalysis', 'add_financialanalysis', 'change_financialanalysis', 'delete_financialanalysis',
    'view_activitycoordination', 'add_activitycoordination', 'change_activitycoordination', 'delete_activitycoordination',
    'view_finalfinancialanalysis', 'add_finalfinancialanalysis', 'change_finalfinancialanalysis', 'delete_finalfinancialanalysis',
    # صلاحيات الاعتماد الخاصة بالمدير
    'approve_activity', 'approve_financialanalysis', 'approve_activitycoordination', 'approve_finalfinancialanalysis',
]


def _grant_role(user, branch, codenames, role_name):
    role = Role.objects.create(name=role_name)
    for codename in codenames:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={'name': codename, 'app_label': 'activities', 'model_name': codename.split('_', 1)[1], 'action': codename.split('_', 1)[0]},
        )
        role.permissions.add(perm)
    EmployeeRole.objects.create(person=user, role=role, branch=branch)


class ActivityWorkflowTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Root Academy')
        self.branch = Branch.objects.create(company=self.company, code=1, name='Main Branch')

        self.employee = Person.objects.create_user(
            email='employee@example.com', password='pass12345',
            first_name='Emp', forth_name='Loyee',
        )
        self.manager = Person.objects.create_user(
            email='manager@example.com', password='pass12345',
            first_name='Man', forth_name='Ager',
        )
        self.stranger = Person.objects.create_user(
            email='stranger@example.com', password='pass12345',
            first_name='Str', forth_name='Anger',
        )

        _grant_role(self.employee, self.branch, ['view_activity', 'add_activity'], 'activity_employee')
        _grant_role(self.manager, self.branch, ACTIVITY_PERMS, 'activity_manager')

        self.employee_client = Client()
        self.employee_client.force_login(self.employee)
        self.manager_client = Client()
        self.manager_client.force_login(self.manager)
        self.stranger_client = Client()
        self.stranger_client.force_login(self.stranger)

    def _contract_payload(self, **overrides):
        payload = {
            'branch': self.branch.pk,
            'form_date': '2025-02-01',
            'name': 'دورة إدارة المشاريع',
            'location': 'قاعة 1',
            'event_date': '2025-03-01',
            'activity_type': 'course',
            'target_audience': 'موظفو الشركات',
            'region': 'central',
            'accreditation_type': 'continuous',
            'expected_attendees': 30,
            'trainer_name': 'د. أحمد',
            'no_partner': 'on',
            'authorized_signatory': 'المفوض الأول',
            'coordinator_name': 'منسق النشاط',
        }
        payload.update(overrides)
        return payload

    def _create_contract(self):
        response = self.employee_client.post(reverse('activity-create'), self._contract_payload())
        self.assertEqual(response.status_code, 302)
        return Activity.objects.get()

    def _approve_contract(self, activity):
        self.employee_client.post(reverse('activity-transition', args=[activity.pk, 'submit']))
        activity.refresh_from_db()
        self.assertEqual(activity.status, StageStatus.PENDING)
        self.manager_client.post(reverse('activity-transition', args=[activity.pk, 'approve']))
        activity.refresh_from_db()
        self.assertEqual(activity.status, StageStatus.APPROVED)

    def _financial_payload(self, **overrides):
        payload = {
            'analysis_date': '2025-02-05',
            'trainee_count': 25,
            'fee_per_trainee': '100.00',
            'actual_trainee_fees': '2600.00',
            'expected_electricity': '50', 'actual_electricity': '60',
            'expected_water': '20', 'actual_water': '20',
            'expected_hall': '200', 'actual_hall': '200',
            'expected_hospitality': '150', 'actual_hospitality': '100',
            'expected_transport': '40', 'actual_transport': '45',
            'expected_certificates': '75', 'actual_certificates': '80',
            'expected_trainer_fee': '500', 'actual_trainer_fee': '500',
            'prepared_by': 'محلل مالي',
            'preparer_job_title': 'محاسب',
        }
        payload.update(overrides)
        return payload

    def _create_and_approve_financial(self, activity):
        response = self.employee_client.post(
            reverse('financial-create', args=[activity.pk]), self._financial_payload()
        )
        self.assertEqual(response.status_code, 302)
        financial = FinancialAnalysis.objects.get(activity=activity)
        self.employee_client.post(reverse('financial-transition', args=[financial.pk, 'submit']))
        self.manager_client.post(reverse('financial-transition', args=[financial.pk, 'approve']))
        financial.refresh_from_db()
        self.assertEqual(financial.status, StageStatus.APPROVED)
        return financial

    def _coordination_payload(self, **overrides):
        payload = {
            'coordination_date': '2025-02-20',
            'lecturer_name': 'د. أحمد',
            'lecturer_phone': '0912345678',
            'coordinator_name': 'منسق النشاط',
            'start_time': '10:00',
            'end_time': '12:00',
            'registered_count': 25,
            'attended_count': 20,
        }
        payload.update(overrides)
        return payload

    # --- إنشاء العقد والمالك ---

    def test_create_contract_sets_owner_and_auto_numbers(self):
        activity = self._create_contract()
        self.assertEqual(activity.created_by, self.employee)
        self.assertEqual(activity.form_number, 1)
        self.assertEqual(activity.request_number, 1)  # يُرقم تلقائيًا
        self.assertEqual(activity.status, StageStatus.DRAFT)
        self.assertTrue(ActivityLog.objects.filter(activity=activity, stage='contract', action='create').exists())

    def test_contract_without_partner_is_valid(self):
        activity = self._create_contract()
        self.assertTrue(activity.no_partner)
        self.assertEqual(activity.effective_partner_percent, Decimal('0.00'))

    def test_contract_requires_partner_name_when_partner_exists(self):
        payload = self._contract_payload()
        payload.pop('no_partner')
        response = self.employee_client.post(reverse('activity-create'), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Activity.objects.exists())

    # --- ترتيب المراحل ---

    def test_financial_blocked_before_contract_approval(self):
        activity = self._create_contract()
        response = self.employee_client.get(reverse('financial-create', args=[activity.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FinancialAnalysis.objects.exists())

    def test_coordination_blocked_before_financial_approval(self):
        activity = self._create_contract()
        self._approve_contract(activity)
        response = self.employee_client.get(reverse('coordination-create', args=[activity.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ActivityCoordination.objects.exists())

    def test_full_workflow_order(self):
        activity = self._create_contract()
        self._approve_contract(activity)

        financial = self._create_and_approve_financial(activity)

        response = self.employee_client.post(
            reverse('coordination-create', args=[activity.pk]), self._coordination_payload()
        )
        self.assertEqual(response.status_code, 302)
        coordination = ActivityCoordination.objects.get(activity=activity)
        self.assertEqual(coordination.created_by, self.employee)
        self.assertEqual(coordination.form_number, 1)

    # --- الصلاحيات والملكية ---

    def test_stranger_cannot_access_anything(self):
        activity = self._create_contract()
        # القائمة تُرفض صراحة، وصفحات الكائنات تخفي نفسها (404) وفق سلوك BranchPermissionMixin
        response = self.stranger_client.get(reverse('activity-list'))
        self.assertEqual(response.status_code, 403)
        for url in [
            reverse('activity-detail', args=[activity.pk]),
            reverse('activity-update', args=[activity.pk]),
        ]:
            response = self.stranger_client.get(url)
            self.assertIn(response.status_code, [403, 404], url)

    def test_stranger_cannot_submit_or_approve(self):
        activity = self._create_contract()
        response = self.stranger_client.post(reverse('activity-transition', args=[activity.pk, 'submit']))
        self.assertEqual(response.status_code, 403)
        activity.refresh_from_db()
        self.assertEqual(activity.status, StageStatus.DRAFT)

    def test_employee_without_change_perm_cannot_approve_own_form(self):
        activity = self._create_contract()
        self.employee_client.post(reverse('activity-transition', args=[activity.pk, 'submit']))
        # الموظف المنشئ ليس لديه صلاحية change_activity — لا يمكنه الاعتماد
        response = self.employee_client.post(reverse('activity-transition', args=[activity.pk, 'approve']))
        self.assertEqual(response.status_code, 403)
        activity.refresh_from_db()
        self.assertEqual(activity.status, StageStatus.PENDING)

    def test_manager_with_change_perm_approves(self):
        activity = self._create_contract()
        self.employee_client.post(reverse('activity-transition', args=[activity.pk, 'submit']))
        self.manager_client.post(reverse('activity-transition', args=[activity.pk, 'approve']))
        activity.refresh_from_db()
        self.assertEqual(activity.status, StageStatus.APPROVED)
        self.assertEqual(activity.approved_by, self.manager)
        self.assertIsNotNone(activity.approved_at)

    def test_pending_form_cannot_be_edited(self):
        activity = self._create_contract()
        self.employee_client.post(reverse('activity-transition', args=[activity.pk, 'submit']))
        response = self.employee_client.get(reverse('activity-update', args=[activity.pk]))
        self.assertEqual(response.status_code, 302)
        activity.refresh_from_db()
        self.assertEqual(activity.status, StageStatus.PENDING)

    def test_approved_form_cannot_be_edited_or_deleted(self):
        activity = self._create_contract()
        self._approve_contract(activity)
        response = self.employee_client.get(reverse('activity-update', args=[activity.pk]))
        self.assertEqual(response.status_code, 302)
        response = self.employee_client.post(reverse('activity-delete', args=[activity.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Activity.objects.filter(pk=activity.pk).exists())

    # --- الرفض وإعادة الفتح ---

    def test_reject_requires_reason_and_reopen_works(self):
        activity = self._create_contract()
        self.employee_client.post(reverse('activity-transition', args=[activity.pk, 'submit']))

        # بدون سبب — يرفض النظام التغيير
        self.manager_client.post(reverse('activity-transition', args=[activity.pk, 'reject']))
        activity.refresh_from_db()
        self.assertEqual(activity.status, StageStatus.PENDING)

        self.manager_client.post(
            reverse('activity-transition', args=[activity.pk, 'reject']),
            {'rejection_reason': 'بيانات الشريك ناقصة'},
        )
        activity.refresh_from_db()
        self.assertEqual(activity.status, StageStatus.REJECTED)
        self.assertEqual(activity.rejection_reason, 'بيانات الشريك ناقصة')
        self.assertTrue(ActivityLog.objects.filter(activity=activity, action='reject').exists())

        self.employee_client.post(reverse('activity-transition', args=[activity.pk, 'reopen']))
        activity.refresh_from_db()
        self.assertEqual(activity.status, StageStatus.DRAFT)

    # --- الحسابات المالية ---

    def test_financial_calculations_with_partner(self):
        activity = self._create_contract()
        # نشاط بشريك 25%
        activity.no_partner = False
        activity.partner_kind = 'person'
        activity.partner_name = 'شريك خارجي'
        activity.partner_share_percent = Decimal('25.00')
        activity.save()
        self._approve_contract(activity)

        response = self.employee_client.post(
            reverse('financial-create', args=[activity.pk]), self._financial_payload()
        )
        self.assertEqual(response.status_code, 302)
        financial = FinancialAnalysis.objects.get(activity=activity)

        # الإيرادات المتوقعة = 25 × 100 = 2500
        self.assertEqual(financial.expected_trainee_fees, Decimal('2500.00'))
        self.assertEqual(financial.expected_total_revenue, Decimal('2500.00'))
        self.assertEqual(financial.actual_total_revenue, Decimal('2600.00'))

        # التكاليف المتوقعة = 50+20+200+150+40+75+500 = 1035
        self.assertEqual(financial.expected_total_costs, Decimal('1035.00'))
        # التكاليف الفعلية = 60+20+200+100+45+80+500 = 1005
        self.assertEqual(financial.actual_total_costs, Decimal('1005.00'))

        # صافي الربح المتوقع = 2500 - 1035 = 1465
        self.assertEqual(financial.expected_net_profit, Decimal('1465.00'))
        # شريك 25%: 1465 × 0.25 = 366.25
        self.assertEqual(financial.expected_partner_share, Decimal('366.25'))
        self.assertEqual(financial.expected_company_share, Decimal('1098.75'))

        # صافي الربح الفعلي = 2600 - 1005 = 1595
        self.assertEqual(financial.actual_net_profit, Decimal('1595.00'))
        self.assertEqual(financial.actual_partner_share, Decimal('398.75'))
        self.assertEqual(financial.actual_company_share, Decimal('1196.25'))

    def test_financial_no_partner_gives_company_full_share(self):
        activity = self._create_contract()  # no_partner=True
        self._approve_contract(activity)
        self.employee_client.post(reverse('financial-create', args=[activity.pk]), self._financial_payload())
        financial = FinancialAnalysis.objects.get(activity=activity)
        self.assertEqual(financial.expected_partner_share, Decimal('0.00'))
        self.assertEqual(financial.expected_company_share, financial.expected_net_profit)

    # --- حضور التنسيق ---

    def test_coordination_attendance_calculations(self):
        activity = self._create_contract()
        self._approve_contract(activity)
        self._create_and_approve_financial(activity)

        response = self.employee_client.post(
            reverse('coordination-create', args=[activity.pk]), self._coordination_payload()
        )
        self.assertEqual(response.status_code, 302)
        coordination = ActivityCoordination.objects.get(activity=activity)
        self.assertEqual(coordination.absent_count, 5)
        self.assertEqual(coordination.attendance_rate, Decimal('80.00'))

    def test_coordination_rejects_attended_above_registered(self):
        activity = self._create_contract()
        self._approve_contract(activity)
        self._create_and_approve_financial(activity)

        response = self.employee_client.post(
            reverse('coordination-create', args=[activity.pk]),
            self._coordination_payload(registered_count=10, attended_count=15),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ActivityCoordination.objects.exists())

    def test_coordination_rejects_end_before_start(self):
        activity = self._create_contract()
        self._approve_contract(activity)
        self._create_and_approve_financial(activity)

        response = self.employee_client.post(
            reverse('coordination-create', args=[activity.pk]),
            self._coordination_payload(start_time='12:00', end_time='10:00'),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ActivityCoordination.objects.exists())

    # --- PDF ---

    def test_pdf_downloads(self):
        activity = self._create_contract()
        self._approve_contract(activity)
        financial = self._create_and_approve_financial(activity)
        self.employee_client.post(
            reverse('coordination-create', args=[activity.pk]), self._coordination_payload()
        )
        coordination = ActivityCoordination.objects.get(activity=activity)

        for url in [
            reverse('activity-pdf', args=[activity.pk]),
            reverse('financial-pdf', args=[financial.pk]),
            reverse('coordination-pdf', args=[coordination.pk]),
        ]:
            response = self.employee_client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertEqual(response['Content-Type'], 'application/pdf', url)
            self.assertTrue(response.content.startswith(b'%PDF'), url)

    def test_stranger_cannot_download_pdf(self):
        activity = self._create_contract()
        response = self.stranger_client.get(reverse('activity-pdf', args=[activity.pk]))
        self.assertEqual(response.status_code, 403)

    # --- السجل ---

    def test_audit_log_records_lifecycle(self):
        activity = self._create_contract()
        self._approve_contract(activity)
        actions = list(
            ActivityLog.objects.filter(activity=activity).values_list('action', flat=True)
        )
        self.assertIn('create', actions)
        self.assertIn('submit', actions)
        self.assertIn('approve', actions)

    # --- المرحلة الرابعة: التحليل المالي النهائي ---

    def _create_and_approve_coordination(self, activity):
        response = self.employee_client.post(
            reverse('coordination-create', args=[activity.pk]), self._coordination_payload()
        )
        self.assertEqual(response.status_code, 302)
        coordination = ActivityCoordination.objects.get(activity=activity)
        self.employee_client.post(reverse('coordination-transition', args=[coordination.pk, 'submit']))
        self.manager_client.post(reverse('coordination-transition', args=[coordination.pk, 'approve']))
        coordination.refresh_from_db()
        self.assertEqual(coordination.status, StageStatus.APPROVED)
        return coordination

    def _final_payload(self, **overrides):
        payload = {
            'analysis_date': '2025-03-11',
            'trainee_count': 20,
            'fee_per_trainee': '100.00',
            'actual_electricity': '60', 'actual_water': '20', 'actual_hall': '200',
            'actual_hospitality': '100', 'actual_transport': '45', 'actual_certificates': '80', 'actual_trainer_fee': '500',
            'prepared_by': 'Emp Loyee',
            'approval_name': 'د. عبدالله',
        }
        payload.update(overrides)
        return payload

    def test_final_blocked_before_coordination_approval(self):
        activity = self._create_contract()
        self._approve_contract(activity)
        response = self.employee_client.get(reverse('final-create', args=[activity.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(FinalFinancialAnalysis.objects.exists())

    def test_final_workflow_and_calculations(self):
        activity = self._create_contract()
        self._approve_contract(activity)

        # معد التحليل = المستخدم الحالي — يظهر اسمه تلقائيًا في النموذج
        response = self.employee_client.get(reverse('financial-create', args=[activity.pk]))
        self.assertContains(response, 'Loyee')

        self._create_and_approve_financial(activity)
        self._create_and_approve_coordination(activity)

        response = self.employee_client.post(
            reverse('final-create', args=[activity.pk]), self._final_payload()
        )
        self.assertEqual(response.status_code, 302)
        final = FinalFinancialAnalysis.objects.get(activity=activity)
        self.assertEqual(final.created_by, self.employee)
        # إيرادات = 20 × 100 = 2000؛ تكاليف = 60+20+200+100+45+80+500 = 1005
        self.assertEqual(final.total_revenue, Decimal('2000.00'))
        self.assertEqual(final.total_costs, Decimal('1005.00'))
        self.assertEqual(final.net_profit, Decimal('995.00'))
        # لا يوجد شريك — الشركة كامل الصافي
        self.assertEqual(final.company_share, Decimal('995.00'))
        self.assertEqual(final.partner_share, Decimal('0.00'))

        # الاعتماد بصلاحية «اعتماد» الخاصة بالمدير
        self.employee_client.post(reverse('final-transition', args=[final.pk, 'submit']))
        final.refresh_from_db()
        self.assertEqual(final.status, StageStatus.PENDING)
        self.manager_client.post(reverse('final-transition', args=[final.pk, 'approve']))
        final.refresh_from_db()
        self.assertEqual(final.status, StageStatus.APPROVED)

        # PDF النهائي
        response = self.employee_client.get(reverse('final-pdf', args=[final.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_final_with_partner_share(self):
        activity = self._create_contract()
        activity.no_partner = False
        activity.partner_kind = 'organization'
        activity.partner_name = 'مؤسسة التميز'
        activity.partner_share_percent = Decimal('25.00')
        activity.save()
        self._approve_contract(activity)
        self._create_and_approve_financial(activity)
        self._create_and_approve_coordination(activity)
        self.employee_client.post(reverse('final-create', args=[activity.pk]), self._final_payload())
        final = FinalFinancialAnalysis.objects.get(activity=activity)
        # صافي 995 — شريك 25% = 248.75
        self.assertEqual(final.partner_share, Decimal('248.75'))
        self.assertEqual(final.company_share, Decimal('746.25'))
