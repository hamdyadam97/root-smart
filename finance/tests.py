from decimal import Decimal

from django.db import connection
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import EmployeeRole, Permission, Person, Role
from core.models import Branch, Company
from .models import DisbursementRequest, DisbursementStatus


def _grant(user, branch, codenames, role_name):
    role = Role.objects.create(name=role_name)
    for codename in codenames:
        perm, _ = Permission.objects.get_or_create(
            codename=codename,
            defaults={'name': codename, 'app_label': 'finance', 'model_name': 'disbursementrequest',
                      'action': codename.split('_', 1)[0]},
        )
        role.permissions.add(perm)
    EmployeeRole.objects.create(person=user, role=role, branch=branch)


class DisbursementTests(TestCase):
    def setUp(self):
        company = Company.objects.create(name='Root Academy')
        self.branch = Branch.objects.create(company=company, code=1, name='Main Branch')
        self.employee = Person.objects.create_user(
            email='emp@example.com', password='pass12345', first_name='Emp', forth_name='One', branch=self.branch)
        self.manager = Person.objects.create_user(
            email='mgr@example.com', password='pass12345', first_name='Man', forth_name='Ager', branch=self.branch)
        _grant(self.employee, self.branch,
               ['view_disbursementrequest', 'add_disbursementrequest', 'change_disbursementrequest'], 'موظف')
        _grant(self.manager, self.branch,
               ['view_disbursementrequest', 'add_disbursementrequest', 'change_disbursementrequest',
                'delete_disbursementrequest', 'approve_disbursementrequest'], 'مدير')

    def client_for(self, user):
        c = Client()
        c.force_login(user)
        return c

    def form_data(self, **extra):
        data = {
            'entity_name': 'مطبعة النور', 'subject': 'طلب صرف', 'date': '2026-11-21T10:00',
            'amount_number': '150.00', 'amount_string': 'مئة وخمسون دينار', 'reason': 'طباعة',
            'payment_method': 'CASH', 'purpose': 'بروشورات', 'requester_name': 'Emp One',
            'requester_job_title': 'موظف', 'requester_signed_name': 'Emp One',
            'supervisor_name': '', 'supervisor_signed_name': '', 'supervisor_signature_date': '',
            'disbursed_date': '', 'disbursed_by_name': '', 'disbursed_signed_name': '', 'notes': '',
            'details-TOTAL_FORMS': '1', 'details-INITIAL_FORMS': '0',
            'details-MIN_NUM_FORMS': '0', 'details-MAX_NUM_FORMS': '1000',
            'details-0-description': 'ورق', 'details-0-amount': '150.00',
        }
        data.update(extra)
        return data

    def test_tables_use_old_finance_names(self):
        self.assertIn('finance_disbursementrequest', connection.introspection.table_names())
        self.assertIn('finance_disbursementdetail', connection.introspection.table_names())

    def test_full_flow_and_manager_edits_after_approval(self):
        emp = self.client_for(self.employee)
        emp.post(reverse('disbursement-create'), self.form_data())
        d = DisbursementRequest.objects.get()
        self.assertEqual(d.request_number, 1)
        self.assertEqual(d.details.count(), 1)

        emp.post(reverse('disbursement-transition', args=[d.pk, 'submit']))
        d.refresh_from_db()
        self.assertEqual(d.status, DisbursementStatus.PENDING)

        self.assertEqual(emp.post(reverse('disbursement-transition', args=[d.pk, 'approve'])).status_code, 403)
        mgr = self.client_for(self.manager)
        mgr.post(reverse('disbursement-transition', args=[d.pk, 'approve']))
        d.refresh_from_db()
        self.assertEqual(d.status, DisbursementStatus.APPROVED)

        # بعد الاعتماد: الموظف لا يعدّل، المدير يعدّل
        update = reverse('disbursement-update', args=[d.pk])
        self.assertRedirects(emp.get(update), reverse('disbursement-detail', args=[d.pk]))
        detail_id = d.details.get().pk
        mgr.post(update, self.form_data(**{
            'amount_number': '200.00', 'details-INITIAL_FORMS': '1', 'details-0-id': str(detail_id),
            'details-0-disbursement': str(d.pk), 'details-0-amount': '200.00',
            'supervisor_name': d.supervisor_name, 'supervisor_signed_name': d.supervisor_signed_name,
            'supervisor_signature_date': d.supervisor_signature_date.isoformat(),
        }))
        d.refresh_from_db()
        self.assertEqual(d.amount_number, Decimal('200.00'))
        self.assertEqual(d.status, DisbursementStatus.APPROVED)

    def test_pages_render_and_menu_link(self):
        d = DisbursementRequest.objects.create(
            entity_name='x', amount_number=10, reason='r', purpose='p', requester_name='n',
            requester_job_title='j', created_by=self.employee, last_person=self.employee)
        mgr = self.client_for(self.manager)
        resp = mgr.get(reverse('disbursement-list'))
        self.assertContains(resp, 'إذن الصرف')
        for name in ('disbursement-create',):
            self.assertEqual(mgr.get(reverse(name)).status_code, 200)
        for name in ('disbursement-detail', 'disbursement-update', 'disbursement-delete'):
            self.assertEqual(mgr.get(reverse(name, args=[d.pk])).status_code, 200)
        stranger = Person.objects.create_user(email='s@example.com', password='pass12345', first_name='S')
        self.assertEqual(self.client_for(stranger).get(reverse('disbursement-list')).status_code, 403)
