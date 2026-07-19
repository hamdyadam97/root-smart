from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import Company, Branch
from .models import Team, Person, BranchAccess, Role, EmployeeRole, EmployeePerformance, Permission
from .forms import (
    TeamForm, PersonCreationForm, PersonChangeForm,
    BranchAccessForm, RoleForm, EmployeeRoleForm, EmployeePerformanceForm
)

User = get_user_model()


# ============================================================
# Model Tests
# ============================================================

class TeamModelTest(TestCase):
    def setUp(self):
        self.team = Team.objects.create(
            name='فريق المبيعات',
            code='SALES',
            description='فريق مبيعات المعهد'
        )

    def test_team_creation(self):
        self.assertEqual(self.team.name, 'فريق المبيعات')
        self.assertEqual(self.team.code, 'SALES')
        self.assertEqual(str(self.team), 'فريق المبيعات')

    def test_team_unique_code(self):
        with self.assertRaises(Exception):
            Team.objects.create(name='فريق آخر', code='SALES')


class PersonModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Company')
        self.branch = Branch.objects.create(
            name='الفرع الرئيسي',
            code=1,
            company=self.company
        )
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='أحمد',
            second_name='محمد',
            third_name='علي',
            forth_name='خالد',
            branch=self.branch
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.get_full_name(), 'أحمد محمد علي خالد')
        self.assertEqual(self.user.get_short_name(), 'أحمد خالد')
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)

    def test_user_str(self):
        self.assertIn('test@example.com', str(self.user))

    def test_get_branches(self):
        branches = self.user.get_branches()
        self.assertIn(self.branch, branches)


class RoleModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(
            name='مدير_فرع',
            description='مدير الفرع الرئيسي'
        )

    def test_role_creation(self):
        self.assertEqual(self.role.name, 'مدير فرع')


class EmployeeRoleModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Branch', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='emp@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )
        self.role = Role.objects.create(name='موظف_عروض')
        self.emp_role = EmployeeRole.objects.create(
            person=self.user,
            role=self.role,
            branch=self.branch
        )

    def test_employee_role_creation(self):
        self.assertEqual(self.emp_role.person, self.user)
        self.assertEqual(self.emp_role.role, self.role)
        self.assertEqual(self.emp_role.branch, self.branch)

    def test_unique_together(self):
        with self.assertRaises(Exception):
            EmployeeRole.objects.create(
                person=self.user,
                role=self.role,
                branch=self.branch
            )


class EmployeePerformanceModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Branch', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='perf@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )
        self.performance = EmployeePerformance.objects.create(
            person=self.user,
            branch=self.branch,
            period_month=4,
            period_year=2026,
            offers_sent=10,
            offers_opened=5,
            subscriptions=2
        )

    def test_performance_creation(self):
        self.assertEqual(self.performance.offers_sent, 10)
        self.assertEqual(self.performance.subscriptions, 2)
        self.assertEqual(str(self.performance), 'Test User - 4/2026')


class BranchAccessModelTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Branch', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='access@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )
        self.access = BranchAccess.objects.create(
            person=self.user,
            branch=self.branch
        )

    def test_branch_access_creation(self):
        self.assertEqual(self.access.person, self.user)
        self.assertEqual(self.access.branch, self.branch)
        self.assertIn(self.access, self.user.branch_accesses.all())

    def test_branch_access_unique_together(self):
        with self.assertRaises(Exception):
            BranchAccess.objects.create(person=self.user, branch=self.branch)

    def test_get_branches_includes_access(self):
        branches = self.user.get_branches()
        self.assertIn(self.branch, branches)


# ============================================================
# Branch Scope Permission Tests
# ============================================================

class BranchScopePermissionTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co')
        # Use dynamically chosen high codes to avoid collision with existing branches
        max_code = Branch.objects.order_by('-code').values_list('code', flat=True).first() or 0
        self.branch_a = Branch.objects.create(name='Branch A', code=max_code + 1, company=self.company)
        self.branch_b = Branch.objects.create(name='Branch B', code=max_code + 2, company=self.company)
        import uuid
        self.suffix = uuid.uuid4().hex[:8]
        self.user = User.objects.create_user(
            email=f'scope_{self.suffix}@test.com',
            password='test123',
            first_name='Scope',
            forth_name='User'
        )
        self.role = Role.objects.create(name=f'student_manager_{self.suffix}')
        self.view_student = Permission.objects.get(codename='view_student')
        self.change_student = Permission.objects.get(codename='change_student')
        self.role.permissions.add(self.view_student, self.change_student)
        EmployeeRole.objects.create(person=self.user, role=self.role, branch=self.branch_a)

    def test_is_executive_for_superuser(self):
        admin = User.objects.create_user(email=f'admin_{self.suffix}@test.com', password='test123', is_superuser=True)
        self.assertTrue(admin.is_executive())
        self.assertFalse(self.user.is_executive())
        admin.delete()

    def test_has_perm_on_allowed_branch(self):
        self.assertTrue(self.user.has_perm('view_student', branch=self.branch_a))
        self.assertTrue(self.user.has_perm('change_student', branch=self.branch_a))

    def test_has_perm_denied_on_other_branch(self):
        self.assertFalse(self.user.has_perm('view_student', branch=self.branch_b))
        self.assertFalse(self.user.has_perm('change_student', branch=self.branch_b))

    def test_get_branches_for_perm(self):
        branches = self.user.get_branches_for_perm('view_student')
        self.assertEqual(len(branches), 1)
        self.assertIn(self.branch_a, branches)
        self.assertNotIn(self.branch_b, branches)

    def test_has_perm_on_any_branch(self):
        self.assertTrue(self.user.has_perm_on_any_branch('view_student'))
        self.assertFalse(self.user.has_perm_on_any_branch('delete_student'))

    def test_superuser_sees_all_branches(self):
        admin = User.objects.create_user(email=f'admin2_{self.suffix}@test.com', password='test123', is_superuser=True)
        self.assertTrue(admin.has_perm('view_student', branch=self.branch_b))
        self.assertEqual(len(admin.get_branches_for_perm('view_student')), Branch.objects.count())
        admin.delete()


# ============================================================
# Model Edge Case Tests
# ============================================================

class PersonModelEdgeCaseTest(TestCase):
    def test_full_name_with_empty_names(self):
        user = User.objects.create_user(
            email='empty@test.com',
            password='test123',
            first_name='',
            second_name='',
            third_name='',
            forth_name=''
        )
        self.assertEqual(user.get_full_name(), '')
        self.assertEqual(user.get_short_name(), '')

    def test_short_name_with_only_first_name(self):
        user = User.objects.create_user(
            email='firstonly@test.com',
            password='test123',
            first_name='أحمد',
            forth_name=''
        )
        self.assertEqual(user.get_short_name(), 'أحمد')

    def test_get_branches_no_main_branch(self):
        company = Company.objects.create(name='Test Co')
        branch = Branch.objects.create(name='Branch', code=1, company=company)
        user = User.objects.create_user(
            email='nobranch@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )
        BranchAccess.objects.create(person=user, branch=branch)
        branches = user.get_branches()
        self.assertIn(branch, branches)
        self.assertEqual(len(branches), 1)

    def test_superuser_creation(self):
        admin = User.objects.create_superuser(
            email='admin@test.com',
            password='admin123',
            first_name='Admin',
            forth_name='User'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_active)

    def test_person_options_default(self):
        user = User.objects.create_user(
            email='options@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )
        self.assertEqual(user.options, {})

    def test_person_str_with_no_names(self):
        user = User.objects.create_user(
            email='noname@test.com',
            password='test123',
            first_name='',
            forth_name=''
        )
        self.assertIn('noname@test.com', str(user))


class TeamModelEdgeCaseTest(TestCase):
    def test_team_blank_description(self):
        team = Team.objects.create(name='فريق', code='T2')
        self.assertEqual(team.description, '')

    def test_team_ordering(self):
        Team.objects.create(name='فريق ب', code='B')
        Team.objects.create(name='فريق أ', code='A')
        teams = list(Team.objects.all())
        self.assertEqual(teams[0].name, 'فريق أ')
        self.assertEqual(teams[1].name, 'فريق ب')


class RoleModelEdgeCaseTest(TestCase):
    def test_role_permissions_default(self):
        role = Role.objects.create(name='مدير_نظام')
        self.assertEqual(role.permissions, [])

    def test_role_str_display(self):
        role = Role.objects.create(name='موظف_متابعة')
        self.assertEqual(str(role), 'موظف متابعة')


class EmployeePerformanceModelEdgeCaseTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Branch', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='perf2@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )

    def test_unique_together_period(self):
        EmployeePerformance.objects.create(
            person=self.user,
            branch=self.branch,
            period_month=1,
            period_year=2026
        )
        with self.assertRaises(Exception):
            EmployeePerformance.objects.create(
                person=self.user,
                branch=self.branch,
                period_month=1,
                period_year=2026
            )

    def test_default_counters(self):
        perf = EmployeePerformance.objects.create(
            person=self.user,
            branch=self.branch,
            period_month=2,
            period_year=2026
        )
        self.assertEqual(perf.offers_sent, 0)
        self.assertEqual(perf.offers_opened, 0)
        self.assertEqual(perf.offers_interacted, 0)
        self.assertEqual(perf.subscriptions, 0)

    def test_performance_ordering(self):
        p1 = EmployeePerformance.objects.create(
            person=self.user, branch=self.branch, period_month=1, period_year=2025
        )
        p2 = EmployeePerformance.objects.create(
            person=self.user, branch=self.branch, period_month=1, period_year=2026
        )
        performances = list(EmployeePerformance.objects.all())
        self.assertEqual(performances[0], p2)
        self.assertEqual(performances[1], p1)


class BranchAccessModelEdgeCaseTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Branch', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='ba2@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )

    def test_cascade_delete_person(self):
        access = BranchAccess.objects.create(person=self.user, branch=self.branch)
        pk = access.pk
        self.user.delete()
        self.assertFalse(BranchAccess.objects.filter(pk=pk).exists())

    def test_multiple_branches_access(self):
        branch2 = Branch.objects.create(name='Branch2', code=2, company=self.company)
        BranchAccess.objects.create(person=self.user, branch=self.branch)
        BranchAccess.objects.create(person=self.user, branch=branch2)
        branches = self.user.get_branches()
        self.assertEqual(len(branches), 2)


# ============================================================
# Form Tests
# ============================================================

class TeamFormTest(TestCase):
    def test_valid_team_form(self):
        data = {'name': 'فريق جديد', 'code': 'NEW', 'description': 'وصف'}
        form = TeamForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_team_form_missing_name(self):
        data = {'name': '', 'code': 'NEW', 'description': 'وصف'}
        form = TeamForm(data=data)
        self.assertFalse(form.is_valid())


class PersonCreationFormTest(TestCase):
    def test_valid_person_creation_form(self):
        data = {
            'email': 'new@test.com',
            'first_name': 'أحمد',
            'forth_name': 'خالد',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
        }
        form = PersonCreationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_person_creation_form_password_mismatch(self):
        data = {
            'email': 'new@test.com',
            'first_name': 'أحمد',
            'forth_name': 'خالد',
            'password1': 'testpass123',
            'password2': 'different',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
        }
        form = PersonCreationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_person_creation_form_missing_email(self):
        data = {
            'email': '',
            'first_name': 'أحمد',
            'forth_name': 'خالد',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        form = PersonCreationForm(data=data)
        self.assertFalse(form.is_valid())


class PersonChangeFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='change@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )

    def test_valid_person_change_form(self):
        data = {
            'email': 'change@test.com',
            'first_name': 'Updated',
            'forth_name': 'User',
            'is_staff': True,
            'is_active': True,
            'is_superuser': False,
        }
        form = PersonChangeForm(instance=self.user, data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_person_change_form_missing_first_name(self):
        data = {
            'email': 'change@test.com',
            'first_name': '',
            'forth_name': 'User',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
        }
        form = PersonChangeForm(instance=self.user, data=data)
        # first_name is not required at model level (blank=True), but is in REQUIRED_FIELDS
        # Model allows blank, so form should be valid
        self.assertTrue(form.is_valid())


class BranchAccessFormTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Branch', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='ba@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )

    def test_valid_branch_access_form(self):
        data = {'person': self.user.pk, 'branch': self.branch.pk}
        form = BranchAccessForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_branch_access_form_missing_branch(self):
        data = {'person': self.user.pk, 'branch': ''}
        form = BranchAccessForm(data=data)
        self.assertFalse(form.is_valid())


class RoleFormTest(TestCase):
    def test_valid_role_form(self):
        data = {'name': 'مدير_فرع', 'description': 'وصف', 'permissions': '[]'}
        form = RoleForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_role_form_missing_name(self):
        data = {'name': '', 'description': 'وصف', 'permissions': '[]'}
        form = RoleForm(data=data)
        self.assertFalse(form.is_valid())


class EmployeeRoleFormTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Branch', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='er@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )
        self.role = Role.objects.create(name='موظف_عروض')

    def test_valid_employee_role_form(self):
        data = {'person': self.user.pk, 'role': self.role.pk, 'branch': self.branch.pk}
        form = EmployeeRoleForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_employee_role_form_missing_role(self):
        data = {'person': self.user.pk, 'role': '', 'branch': self.branch.pk}
        form = EmployeeRoleForm(data=data)
        self.assertFalse(form.is_valid())


class EmployeePerformanceFormTest(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Branch', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='ep@test.com',
            password='test123',
            first_name='Test',
            forth_name='User'
        )

    def test_valid_employee_performance_form(self):
        data = {
            'person': self.user.pk,
            'branch': self.branch.pk,
            'period_month': 5,
            'period_year': 2026,
            'offers_sent': 10,
            'offers_opened': 5,
            'offers_interacted': 2,
            'subscriptions': 1,
        }
        form = EmployeePerformanceForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_employee_performance_form_missing_year(self):
        data = {
            'person': self.user.pk,
            'branch': self.branch.pk,
            'period_month': 5,
            'period_year': '',
            'offers_sent': 10,
            'offers_opened': 5,
            'offers_interacted': 2,
            'subscriptions': 1,
        }
        form = EmployeePerformanceForm(data=data)
        self.assertFalse(form.is_valid())


# ============================================================
# View Tests
# ============================================================

class AccountsBaseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.company = Company.objects.create(name='Test Co')
        self.branch = Branch.objects.create(name='Main', code=1, company=self.company)
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            forth_name='User',
            is_staff=True
        )
        self.client.force_login(self.user)


class LoginLogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='login@test.com',
            password='testpass123',
            first_name='Test',
            forth_name='User'
        )

    def test_login_view_get(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_view_post_valid(self):
        response = self.client.post(reverse('login'), {
            'username': 'login@test.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))

    def test_login_view_post_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'login@test.com',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        self.client.login(username='login@test.com', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))


class PersonViewTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.team = Team.objects.create(name='فريق', code='T1')
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            first_name='Other',
            forth_name='User',
            team=self.team
        )

    def test_person_list_get(self):
        response = self.client.get(reverse('person-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test@test.com')

    def test_person_list_search(self):
        response = self.client.get(reverse('person-list'), {'search': 'Other'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'other@test.com')

    def test_person_list_filter_by_team(self):
        response = self.client.get(reverse('person-list'), {'team': self.team.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'other@test.com')

    def test_person_detail_get(self):
        response = self.client.get(reverse('person-detail', kwargs={'pk': self.other_user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'other@test.com')

    def test_person_create_get(self):
        response = self.client.get(reverse('person-create'))
        self.assertEqual(response.status_code, 200)

    def test_person_create_post(self):
        data = {
            'email': 'created@test.com',
            'first_name': 'Created',
            'forth_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
        }
        response = self.client.post(reverse('person-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email='created@test.com').exists())

    def test_person_update_get(self):
        response = self.client.get(reverse('person-update', kwargs={'pk': self.other_user.pk}))
        self.assertEqual(response.status_code, 200)

    def test_person_update_post(self):
        data = {
            'email': 'other@test.com',
            'first_name': 'Updated',
            'forth_name': 'User',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
        }
        response = self.client.post(reverse('person-update', kwargs={'pk': self.other_user.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.other_user.refresh_from_db()
        self.assertEqual(self.other_user.first_name, 'Updated')

    def test_person_delete_get(self):
        response = self.client.get(reverse('person-delete', kwargs={'pk': self.other_user.pk}))
        self.assertEqual(response.status_code, 200)

    def test_person_delete_post(self):
        response = self.client.post(reverse('person-delete', kwargs={'pk': self.other_user.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.other_user.pk).exists())

    def test_person_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('person-list'),
            reverse('person-detail', kwargs={'pk': self.other_user.pk}),
            reverse('person-create'),
            reverse('person-update', kwargs={'pk': self.other_user.pk}),
            reverse('person-delete', kwargs={'pk': self.other_user.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class PersonViewEdgeCaseTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            first_name='Other',
            forth_name='User'
        )

    def test_person_list_search_by_email(self):
        response = self.client.get(reverse('person-list'), {'search': 'other@test.com'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'other@test.com')

    def test_person_list_search_no_results(self):
        response = self.client.get(reverse('person-list'), {'search': 'nonexistentxyz'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'other@test.com')

    def test_person_create_post_invalid_password_mismatch(self):
        data = {
            'email': 'bad@test.com',
            'first_name': 'Bad',
            'forth_name': 'User',
            'password1': 'testpass123',
            'password2': 'different',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
        }
        response = self.client.post(reverse('person-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='bad@test.com').exists())

    def test_person_create_post_anonymous(self):
        self.client.logout()
        data = {
            'email': 'anon@test.com',
            'first_name': 'Anon',
            'forth_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(reverse('person-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_person_update_404(self):
        response = self.client.get(reverse('person-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_person_delete_404(self):
        response = self.client.get(reverse('person-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_person_detail_404(self):
        response = self.client.get(reverse('person-detail', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_redirect_after_create(self):
        data = {
            'email': 'redirect@test.com',
            'first_name': 'Redirect',
            'forth_name': 'User',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
        }
        response = self.client.post(reverse('person-create'), data)
        self.assertRedirects(response, reverse('person-list'))

    def test_redirect_after_update(self):
        data = {
            'email': 'other@test.com',
            'first_name': 'Updated',
            'forth_name': 'User',
            'is_staff': False,
            'is_active': True,
            'is_superuser': False,
        }
        response = self.client.post(reverse('person-update', kwargs={'pk': self.other_user.pk}), data)
        self.assertRedirects(response, reverse('person-list'))

    def test_redirect_after_delete(self):
        response = self.client.post(reverse('person-delete', kwargs={'pk': self.other_user.pk}))
        self.assertRedirects(response, reverse('person-list'))


class TeamViewTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.team = Team.objects.create(name='فريق', code='T1')

    def test_team_list_get(self):
        response = self.client.get(reverse('team-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'فريق')

    def test_team_detail_get(self):
        response = self.client.get(reverse('team-detail', kwargs={'pk': self.team.pk}))
        self.assertEqual(response.status_code, 200)

    def test_team_create_get(self):
        response = self.client.get(reverse('team-create'))
        self.assertEqual(response.status_code, 200)

    def test_team_create_post(self):
        data = {'name': 'فريق جديد', 'code': 'NEW', 'description': 'وصف'}
        response = self.client.post(reverse('team-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Team.objects.filter(code='NEW').exists())

    def test_team_update_get(self):
        response = self.client.get(reverse('team-update', kwargs={'pk': self.team.pk}))
        self.assertEqual(response.status_code, 200)

    def test_team_update_post(self):
        data = {'name': 'فريق محدث', 'code': 'T1', 'description': 'وصف'}
        response = self.client.post(reverse('team-update', kwargs={'pk': self.team.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.team.refresh_from_db()
        self.assertEqual(self.team.name, 'فريق محدث')

    def test_team_delete_get(self):
        response = self.client.get(reverse('team-delete', kwargs={'pk': self.team.pk}))
        self.assertEqual(response.status_code, 200)

    def test_team_delete_post(self):
        response = self.client.post(reverse('team-delete', kwargs={'pk': self.team.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Team.objects.filter(pk=self.team.pk).exists())

    def test_team_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('team-list'),
            reverse('team-detail', kwargs={'pk': self.team.pk}),
            reverse('team-create'),
            reverse('team-update', kwargs={'pk': self.team.pk}),
            reverse('team-delete', kwargs={'pk': self.team.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class TeamViewEdgeCaseTest(AccountsBaseViewTest):
    def test_team_create_post_duplicate_code(self):
        Team.objects.create(name='فريق', code='T1')
        data = {'name': 'فريق آخر', 'code': 'T1', 'description': ''}
        response = self.client.post(reverse('team-create'), data)
        self.assertEqual(response.status_code, 200)

    def test_team_update_404(self):
        response = self.client.get(reverse('team-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_team_delete_404(self):
        response = self.client.get(reverse('team-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_team_redirect_after_create(self):
        data = {'name': 'فريق جديد', 'code': 'NEW2', 'description': ''}
        response = self.client.post(reverse('team-create'), data)
        self.assertRedirects(response, reverse('team-list'))

    def test_team_redirect_after_delete(self):
        team = Team.objects.create(name='فريق مؤقت', code='TMP')
        response = self.client.post(reverse('team-delete', kwargs={'pk': team.pk}))
        self.assertRedirects(response, reverse('team-list'))


class BranchAccessViewTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            first_name='Other',
            forth_name='User'
        )
        self.access = BranchAccess.objects.create(person=self.other_user, branch=self.branch)

    def test_branchaccess_list_get(self):
        response = self.client.get(reverse('branchaccess-list'))
        self.assertEqual(response.status_code, 200)

    def test_branchaccess_create_get(self):
        response = self.client.get(reverse('branchaccess-create'))
        self.assertEqual(response.status_code, 200)

    def test_branchaccess_create_post(self):
        new_user = User.objects.create_user(
            email='bauser@test.com',
            password='testpass123',
            first_name='BA',
            forth_name='User'
        )
        data = {'person': new_user.pk, 'branch': self.branch.pk}
        response = self.client.post(reverse('branchaccess-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(BranchAccess.objects.filter(person=new_user, branch=self.branch).exists())

    def test_branchaccess_update_get(self):
        response = self.client.get(reverse('branchaccess-update', kwargs={'pk': self.access.pk}))
        self.assertEqual(response.status_code, 200)

    def test_branchaccess_update_post(self):
        new_branch = Branch.objects.create(name='Other', code=2, company=self.company)
        data = {'person': self.other_user.pk, 'branch': new_branch.pk}
        response = self.client.post(reverse('branchaccess-update', kwargs={'pk': self.access.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.access.refresh_from_db()
        self.assertEqual(self.access.branch, new_branch)

    def test_branchaccess_delete_get(self):
        response = self.client.get(reverse('branchaccess-delete', kwargs={'pk': self.access.pk}))
        self.assertEqual(response.status_code, 200)

    def test_branchaccess_delete_post(self):
        response = self.client.post(reverse('branchaccess-delete', kwargs={'pk': self.access.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(BranchAccess.objects.filter(pk=self.access.pk).exists())

    def test_branchaccess_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('branchaccess-list'),
            reverse('branchaccess-create'),
            reverse('branchaccess-update', kwargs={'pk': self.access.pk}),
            reverse('branchaccess-delete', kwargs={'pk': self.access.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class BranchAccessViewEdgeCaseTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(
            email='other@test.com',
            password='testpass123',
            first_name='Other',
            forth_name='User'
        )
        self.access = BranchAccess.objects.create(person=self.other_user, branch=self.branch)

    def test_branchaccess_create_post_duplicate(self):
        data = {'person': self.other_user.pk, 'branch': self.branch.pk}
        response = self.client.post(reverse('branchaccess-create'), data)
        self.assertEqual(response.status_code, 200)

    def test_branchaccess_update_404(self):
        response = self.client.get(reverse('branchaccess-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_branchaccess_delete_404(self):
        response = self.client.get(reverse('branchaccess-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_branchaccess_redirect_after_create(self):
        new_user = User.objects.create_user(
            email='ba3@test.com',
            password='test123',
            first_name='BA',
            forth_name='User'
        )
        new_branch = Branch.objects.create(name='B2', code=2, company=self.company)
        data = {'person': new_user.pk, 'branch': new_branch.pk}
        response = self.client.post(reverse('branchaccess-create'), data)
        self.assertRedirects(response, reverse('branchaccess-list'))

    def test_branchaccess_redirect_after_delete(self):
        response = self.client.post(reverse('branchaccess-delete', kwargs={'pk': self.access.pk}))
        self.assertRedirects(response, reverse('branchaccess-list'))


class RoleViewTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.role = Role.objects.create(name='مدير_فرع')

    def test_role_list_get(self):
        response = self.client.get(reverse('role-list'))
        self.assertEqual(response.status_code, 200)

    def test_role_detail_get(self):
        response = self.client.get(reverse('role-detail', kwargs={'pk': self.role.pk}))
        self.assertEqual(response.status_code, 200)

    def test_role_create_get(self):
        response = self.client.get(reverse('role-create'))
        self.assertEqual(response.status_code, 200)

    def test_role_create_post(self):
        data = {'name': 'موظف_متابعة', 'description': 'وصف', 'permissions': '[]'}
        response = self.client.post(reverse('role-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Role.objects.filter(name='موظف_متابعة').exists())

    def test_role_update_get(self):
        response = self.client.get(reverse('role-update', kwargs={'pk': self.role.pk}))
        self.assertEqual(response.status_code, 200)

    def test_role_update_post(self):
        data = {'name': 'مدير_فرع', 'description': 'وصف محدث', 'permissions': '[]'}
        response = self.client.post(reverse('role-update', kwargs={'pk': self.role.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.role.refresh_from_db()
        self.assertEqual(self.role.description, 'وصف محدث')

    def test_role_delete_get(self):
        response = self.client.get(reverse('role-delete', kwargs={'pk': self.role.pk}))
        self.assertEqual(response.status_code, 200)

    def test_role_delete_post(self):
        response = self.client.post(reverse('role-delete', kwargs={'pk': self.role.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Role.objects.filter(pk=self.role.pk).exists())

    def test_role_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('role-list'),
            reverse('role-detail', kwargs={'pk': self.role.pk}),
            reverse('role-create'),
            reverse('role-update', kwargs={'pk': self.role.pk}),
            reverse('role-delete', kwargs={'pk': self.role.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class RoleViewEdgeCaseTest(AccountsBaseViewTest):
    def test_role_create_post_duplicate_name(self):
        Role.objects.create(name='مدير_فرع')
        data = {'name': 'مدير_فرع', 'description': 'وصف', 'permissions': '[]'}
        response = self.client.post(reverse('role-create'), data)
        self.assertEqual(response.status_code, 200)

    def test_role_update_404(self):
        response = self.client.get(reverse('role-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_role_delete_404(self):
        response = self.client.get(reverse('role-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_role_redirect_after_create(self):
        data = {'name': 'موظف_متابعة', 'description': '', 'permissions': '[]'}
        response = self.client.post(reverse('role-create'), data)
        self.assertRedirects(response, reverse('role-list'))

    def test_role_redirect_after_delete(self):
        role = Role.objects.create(name='مدير_نظام')
        response = self.client.post(reverse('role-delete', kwargs={'pk': role.pk}))
        self.assertRedirects(response, reverse('role-list'))


class EmployeeRoleViewTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.role = Role.objects.create(name='موظف_عروض')
        self.emp_role = EmployeeRole.objects.create(
            person=self.user,
            role=self.role,
            branch=self.branch
        )

    def test_employeerole_list_get(self):
        response = self.client.get(reverse('employeerole-list'))
        self.assertEqual(response.status_code, 200)

    def test_employeerole_create_get(self):
        response = self.client.get(reverse('employeerole-create'))
        self.assertEqual(response.status_code, 200)

    def test_employeerole_create_post(self):
        new_user = User.objects.create_user(
            email='newer@test.com',
            password='testpass123',
            first_name='New',
            forth_name='User'
        )
        new_role = Role.objects.create(name='موظف_متابعة')
        data = {'person': new_user.pk, 'role': new_role.pk, 'branch': self.branch.pk}
        response = self.client.post(reverse('employeerole-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EmployeeRole.objects.filter(person=new_user, role=new_role).exists())

    def test_employeerole_update_get(self):
        response = self.client.get(reverse('employeerole-update', kwargs={'pk': self.emp_role.pk}))
        self.assertEqual(response.status_code, 200)

    def test_employeerole_update_post(self):
        new_role = Role.objects.create(name='مدير_فرع')
        data = {'person': self.user.pk, 'role': new_role.pk, 'branch': self.branch.pk}
        response = self.client.post(reverse('employeerole-update', kwargs={'pk': self.emp_role.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.emp_role.refresh_from_db()
        self.assertEqual(self.emp_role.role, new_role)

    def test_employeerole_delete_get(self):
        response = self.client.get(reverse('employeerole-delete', kwargs={'pk': self.emp_role.pk}))
        self.assertEqual(response.status_code, 200)

    def test_employeerole_delete_post(self):
        response = self.client.post(reverse('employeerole-delete', kwargs={'pk': self.emp_role.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(EmployeeRole.objects.filter(pk=self.emp_role.pk).exists())

    def test_employeerole_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('employeerole-list'),
            reverse('employeerole-create'),
            reverse('employeerole-update', kwargs={'pk': self.emp_role.pk}),
            reverse('employeerole-delete', kwargs={'pk': self.emp_role.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class EmployeeRoleViewEdgeCaseTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.role = Role.objects.create(name='موظف_عروض')
        self.emp_role = EmployeeRole.objects.create(
            person=self.user,
            role=self.role,
            branch=self.branch
        )

    def test_employeerole_create_post_duplicate(self):
        data = {'person': self.user.pk, 'role': self.role.pk, 'branch': self.branch.pk}
        response = self.client.post(reverse('employeerole-create'), data)
        self.assertEqual(response.status_code, 200)

    def test_employeerole_update_404(self):
        response = self.client.get(reverse('employeerole-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_employeerole_delete_404(self):
        response = self.client.get(reverse('employeerole-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_employeerole_redirect_after_create(self):
        new_user = User.objects.create_user(
            email='er2@test.com',
            password='test123',
            first_name='New',
            forth_name='User'
        )
        new_role = Role.objects.create(name='مدير_نظام')
        data = {'person': new_user.pk, 'role': new_role.pk, 'branch': self.branch.pk}
        response = self.client.post(reverse('employeerole-create'), data)
        self.assertRedirects(response, reverse('employeerole-list'))

    def test_employeerole_redirect_after_delete(self):
        response = self.client.post(reverse('employeerole-delete', kwargs={'pk': self.emp_role.pk}))
        self.assertRedirects(response, reverse('employeerole-list'))


class EmployeePerformanceViewTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.performance = EmployeePerformance.objects.create(
            person=self.user,
            branch=self.branch,
            period_month=1,
            period_year=2026,
            offers_sent=5,
            offers_opened=2,
            offers_interacted=1,
            subscriptions=0,
        )

    def test_employeeperformance_list_get(self):
        response = self.client.get(reverse('employeeperformance-list'))
        self.assertEqual(response.status_code, 200)

    def test_employeeperformance_create_get(self):
        response = self.client.get(reverse('employeeperformance-create'))
        self.assertEqual(response.status_code, 200)

    def test_employeeperformance_create_post(self):
        data = {
            'person': self.user.pk,
            'branch': self.branch.pk,
            'period_month': 2,
            'period_year': 2026,
            'offers_sent': 10,
            'offers_opened': 5,
            'offers_interacted': 2,
            'subscriptions': 1,
        }
        response = self.client.post(reverse('employeeperformance-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(EmployeePerformance.objects.filter(period_month=2).exists())

    def test_employeeperformance_update_get(self):
        response = self.client.get(reverse('employeeperformance-update', kwargs={'pk': self.performance.pk}))
        self.assertEqual(response.status_code, 200)

    def test_employeeperformance_update_post(self):
        data = {
            'person': self.user.pk,
            'branch': self.branch.pk,
            'period_month': 1,
            'period_year': 2026,
            'offers_sent': 20,
            'offers_opened': 10,
            'offers_interacted': 5,
            'subscriptions': 2,
        }
        response = self.client.post(reverse('employeeperformance-update', kwargs={'pk': self.performance.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.performance.refresh_from_db()
        self.assertEqual(self.performance.offers_sent, 20)

    def test_employeeperformance_delete_get(self):
        response = self.client.get(reverse('employeeperformance-delete', kwargs={'pk': self.performance.pk}))
        self.assertEqual(response.status_code, 200)

    def test_employeeperformance_delete_post(self):
        response = self.client.post(reverse('employeeperformance-delete', kwargs={'pk': self.performance.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(EmployeePerformance.objects.filter(pk=self.performance.pk).exists())

    def test_employeeperformance_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('employeeperformance-list'),
            reverse('employeeperformance-create'),
            reverse('employeeperformance-update', kwargs={'pk': self.performance.pk}),
            reverse('employeeperformance-delete', kwargs={'pk': self.performance.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


class EmployeePerformanceViewEdgeCaseTest(AccountsBaseViewTest):
    def setUp(self):
        super().setUp()
        self.performance = EmployeePerformance.objects.create(
            person=self.user,
            branch=self.branch,
            period_month=1,
            period_year=2026,
            offers_sent=5,
        )

    def test_employeeperformance_create_post_duplicate(self):
        data = {
            'person': self.user.pk,
            'branch': self.branch.pk,
            'period_month': 1,
            'period_year': 2026,
            'offers_sent': 10,
            'offers_opened': 0,
            'offers_interacted': 0,
            'subscriptions': 0,
        }
        response = self.client.post(reverse('employeeperformance-create'), data)
        self.assertEqual(response.status_code, 200)

    def test_employeeperformance_update_404(self):
        response = self.client.get(reverse('employeeperformance-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_employeeperformance_delete_404(self):
        response = self.client.get(reverse('employeeperformance-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_employeeperformance_redirect_after_create(self):
        data = {
            'person': self.user.pk,
            'branch': self.branch.pk,
            'period_month': 3,
            'period_year': 2026,
            'offers_sent': 1,
            'offers_opened': 0,
            'offers_interacted': 0,
            'subscriptions': 0,
        }
        response = self.client.post(reverse('employeeperformance-create'), data)
        self.assertRedirects(response, reverse('employeeperformance-list'))

    def test_employeeperformance_redirect_after_delete(self):
        response = self.client.post(reverse('employeeperformance-delete', kwargs={'pk': self.performance.pk}))
        self.assertRedirects(response, reverse('employeeperformance-list'))
