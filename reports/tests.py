from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import Company, Branch
from .models import ReportSnapshot

User = get_user_model()


class ReportSnapshotModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='t@t.com', password='123', first_name='A', forth_name='B'
        )
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Main', code=1, company=self.company)

    def test_create_report_snapshot(self):
        report = ReportSnapshot.objects.create(
            report_type='summary',
            branch=self.branch,
            period='2024-01',
            generated_by=self.user,
            data_json={'key': 'value'},
        )
        self.assertEqual(report.report_type, 'summary')
        self.assertEqual(report.branch, self.branch)
        self.assertEqual(report.period, '2024-01')
        self.assertEqual(report.generated_by, self.user)
        self.assertEqual(report.data_json, {'key': 'value'})

    def test_str_method(self):
        report = ReportSnapshot.objects.create(
            report_type='offers',
            period='2024-Q1',
            generated_by=self.user,
        )
        expected = f"{report.get_report_type_display()} - 2024-Q1"
        self.assertEqual(str(report), expected)

    def test_report_type_choices_validation(self):
        valid_choices = [choice[0] for choice in ReportSnapshot.REPORT_TYPE_CHOICES]
        for choice in valid_choices:
            report = ReportSnapshot.objects.create(
                report_type=choice,
                period='2024',
                generated_by=self.user,
            )
            self.assertEqual(report.report_type, choice)

    def test_branch_null_allowed(self):
        report = ReportSnapshot.objects.create(
            report_type='summary',
            branch=None,
            period='2024',
            generated_by=self.user,
        )
        self.assertIsNone(report.branch)

    def test_ordering(self):
        report1 = ReportSnapshot.objects.create(
            report_type='summary', period='First', generated_by=self.user
        )
        report2 = ReportSnapshot.objects.create(
            report_type='offers', period='Second', generated_by=self.user
        )
        reports = list(ReportSnapshot.objects.all())
        self.assertEqual(reports[0], report2)
        self.assertEqual(reports[1], report1)


class ReportSnapshotViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='t@t.com', password='123', first_name='A', forth_name='B'
        )
        self.user2 = User.objects.create_user(
            email='t2@t.com', password='123', first_name='C', forth_name='D'
        )
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Main', code=1, company=self.company)
        self.report = ReportSnapshot.objects.create(
            report_type='summary',
            branch=self.branch,
            period='2024-01',
            generated_by=self.user,
            data_json={'students': 10},
        )

    def test_list_view_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(reverse('reportsnapshot-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('reports', response.context)

    def test_list_view_search(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(reverse('reportsnapshot-list'), {'q': 'summary'})
        self.assertEqual(response.status_code, 200)

    def test_detail_view_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(
            reverse('reportsnapshot-detail', kwargs={'slug': self.report.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('report', response.context)

    def test_create_view_get_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(reverse('reportsnapshot-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_view_post_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        data = {
            'report_type': 'students',
            'branch': self.branch.pk,
            'period': '2024-02',
        }
        response = self.client.post(reverse('reportsnapshot-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            ReportSnapshot.objects.filter(period='2024-02').exists()
        )
        report = ReportSnapshot.objects.get(period='2024-02')
        self.assertEqual(report.generated_by, self.user)
        self.assertEqual(report.report_type, 'students')

    def test_update_view_get_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(
            reverse('reportsnapshot-update', kwargs={'slug': self.report.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_update_view_post_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        data = {
            'report_type': 'employees',
            'branch': self.branch.pk,
            'period': '2024-Updated',
        }
        response = self.client.post(
            reverse('reportsnapshot-update', kwargs={'slug': self.report.slug}), data
        )
        self.assertEqual(response.status_code, 302)
        self.report.refresh_from_db()
        self.assertEqual(self.report.period, '2024-Updated')
        self.assertEqual(self.report.report_type, 'employees')

    def test_delete_view_get_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(
            reverse('reportsnapshot-delete', kwargs={'slug': self.report.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_view_post_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.post(
            reverse('reportsnapshot-delete', kwargs={'slug': self.report.slug})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ReportSnapshot.objects.filter(pk=self.report.pk).exists()
        )

    def test_list_view_redirects_anonymous(self):
        response = self.client.get(reverse('reportsnapshot-list'))
        self.assertEqual(response.status_code, 302)

    def test_detail_view_redirects_anonymous(self):
        response = self.client.get(
            reverse('reportsnapshot-detail', kwargs={'slug': self.report.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_create_view_redirects_anonymous(self):
        response = self.client.get(reverse('reportsnapshot-create'))
        self.assertEqual(response.status_code, 302)

    def test_update_view_redirects_anonymous(self):
        response = self.client.get(
            reverse('reportsnapshot-update', kwargs={'slug': self.report.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_view_redirects_anonymous(self):
        response = self.client.get(
            reverse('reportsnapshot-delete', kwargs={'slug': self.report.slug})
        )
        self.assertEqual(response.status_code, 302)
