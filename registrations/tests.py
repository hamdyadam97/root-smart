from decimal import Decimal

from django.db.models import ProtectedError
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Company, Branch
from courses.models import Master, Course
from students.models import Contact, Student
from finance.models import Payment

from .models import Account, AttachType, Attach, AccountAttach, AccountCondition, AccountNote
from .forms import (
    AccountForm, AttachTypeForm, AttachForm,
    AccountAttachForm, AccountConditionForm, AccountNoteForm,
)


User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com', password='test123',
            first_name='Test', forth_name='User',
            is_staff=True
        )
        self.client.force_login(self.user)

        self.company = Company.objects.create(name='Test Company')
        self.branch = Branch.objects.create(company=self.company, code=1, name='Main Branch')
        self.master = Master.objects.create(branch=self.branch, code=10, name='Test Master')
        self.course = Course.objects.create(master=self.master, code=100)

        self.contact = Contact.objects.create(first_name='Ali', forth_name='Ahmed')
        self.student = Student.objects.create(contact=self.contact)


class AccountModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course,
            student=self.student,
            code=1,
            course_payment_type=Account.PAYMENT_TYPE_CASH,
            course_price=Decimal('1000.00'),
            course_discount_amount=Decimal('10.00'),
            course_profit_amount=Decimal('5.00'),
            course_credit_amount=Decimal('0.00'),
        )

    def test_creation(self):
        self.assertEqual(Account.objects.count(), 1)
        self.assertEqual(self.account.course, self.course)
        self.assertEqual(self.account.student, self.student)

    def test_str(self):
        expected = f"{self.account.get_key()} - {self.student.get_full_name()}"
        self.assertEqual(str(self.account), expected)

    def test_get_key_format(self):
        year_shortcut = str(self.account.register_date.year)[-2:]
        expected = f"{year_shortcut}-{self.branch.code}-{self.master.code}-{self.course.code}-{self.account.code}"
        self.assertEqual(self.account.get_key(), expected)

    def test_get_key_rtl_format(self):
        year_shortcut = str(self.account.register_date.year)[-2:]
        expected = f"{self.account.code}-{self.course.code}-{self.master.code}-{self.branch.code}-{year_shortcut}"
        self.assertEqual(self.account.get_key_rtl(), expected)

    def test_get_required_price_cash(self):
        self.account.course_payment_type = Account.PAYMENT_TYPE_CASH
        self.account.save()
        expected = Decimal('1000.00') - (Decimal('1000.00') * Decimal('10.00') / Decimal('100'))
        self.assertEqual(self.account.get_required_price(), expected)

    def test_get_required_price_installment(self):
        self.account.course_payment_type = Account.PAYMENT_TYPE_INSTALLMENT
        self.account.save()
        expected = Decimal('1000.00') + (Decimal('1000.00') * Decimal('5.00') / Decimal('100'))
        self.assertEqual(self.account.get_required_price(), expected)

    def test_get_paid_price(self):
        Payment.objects.create(
            account=self.account,
            code=1,
            amount_number=Decimal('200.00'),
            type='ايرادات اساسية',
        )
        Payment.objects.create(
            account=self.account,
            code=2,
            amount_number=Decimal('100.00'),
            type='ايرادات اساسية',
        )
        Payment.objects.create(
            account=self.account,
            code=3,
            amount_number=Decimal('50.00'),
            type='ايرادات اخرى',
        )
        self.assertEqual(self.account.get_paid_price(), Decimal('300.00'))

    def test_get_remain_price(self):
        self.account.course_payment_type = Account.PAYMENT_TYPE_CASH
        self.account.save()
        Payment.objects.create(
            account=self.account,
            code=1,
            amount_number=Decimal('200.00'),
            type='ايرادات اساسية',
        )
        required = self.account.get_required_price()
        remain = required - Decimal('200.00')
        self.assertEqual(self.account.get_remain_price(), remain)

    def test_unique_together_course_code(self):
        with self.assertRaises(Exception):
            Account.objects.create(
                course=self.course,
                student=self.student,
                code=1,
            )

    def test_course_protect(self):
        with self.assertRaises(ProtectedError):
            self.course.delete()

    def test_student_protect(self):
        with self.assertRaises(ProtectedError):
            self.student.delete()


class AttachTypeModelTests(BaseTestCase):
    def test_creation_and_str(self):
        at = AttachType.objects.create(name='ID Card', code='ID001')
        self.assertEqual(str(at), 'ID Card')

    def test_unique_code(self):
        AttachType.objects.create(name='ID Card', code='ID001')
        with self.assertRaises(Exception):
            AttachType.objects.create(name='Passport', code='ID001')


class AttachModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.attach_type = AttachType.objects.create(name='ID Card', code='ID001')
        self.attach = Attach.objects.create(
            attach_type=self.attach_type,
            person=self.user,
            title='My ID',
            file_data='data',
            file_name='id.png',
            file_type='image/png',
        )

    def test_creation_and_str(self):
        self.assertEqual(str(self.attach), 'My ID')

    def test_attach_type_protect(self):
        with self.assertRaises(ProtectedError):
            self.attach_type.delete()


class AccountAttachModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course, student=self.student, code=1
        )
        self.attach_type = AttachType.objects.create(name='ID Card', code='ID001')
        self.attach = Attach.objects.create(
            attach_type=self.attach_type,
            person=self.user,
            title='My ID',
            file_data='data',
            file_name='id.png',
            file_type='image/png',
        )
        self.account_attach = AccountAttach.objects.create(
            account=self.account,
            attach=self.attach,
        )

    def test_creation_and_str(self):
        expected = f"{self.account.get_key()} - {self.attach.title}"
        self.assertEqual(str(self.account_attach), expected)


class AccountConditionModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course, student=self.student, code=1
        )
        self.condition = AccountCondition.objects.create(
            account=self.account,
            person=self.user,
            title='Payment Proof',
            content='Submit payment proof',
            fulfilled=False,
        )

    def test_creation_and_str(self):
        expected = f"{self.account.get_key()} - {self.condition.title}"
        self.assertEqual(str(self.condition), expected)

    def test_fulfilled_default(self):
        self.assertFalse(self.condition.fulfilled)


class AccountNoteModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course, student=self.student, code=1
        )
        self.note = AccountNote.objects.create(
            account=self.account,
            person=self.user,
            content='This is a test note for the account registration',
        )

    def test_creation_and_str(self):
        expected = f"{self.account.get_key()} - {self.note.content[:50]}"
        self.assertEqual(str(self.note), expected)


class AccountFormTests(BaseTestCase):
    def test_valid_form(self):
        data = {
            'course': self.course.id,
            'student': self.student.id,
            'code': 99,
            'register_date': '2024-01-01T10:00',
            'course_payment_type': Account.PAYMENT_TYPE_CASH,
            'course_price': '1000.00',
            'course_discount_amount': '0.00',
            'course_profit_amount': '0.00',
            'course_credit_amount': '0.00',
            'note': '',
        }
        form = AccountForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_required(self):
        data = {
            'course': '',
            'student': '',
            'code': '',
        }
        form = AccountForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('course', form.errors)
        self.assertIn('student', form.errors)
        self.assertIn('code', form.errors)


class AttachTypeFormTests(BaseTestCase):
    def test_valid_form(self):
        data = {'name': 'Passport', 'code': 'PASS01', 'description': 'Passport copy'}
        form = AttachTypeForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_name(self):
        data = {'name': '', 'code': 'PASS01'}
        form = AttachTypeForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


class AttachFormTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.attach_type = AttachType.objects.create(name='ID Card', code='ID001')

    def test_valid_form(self):
        data = {
            'attach_type': self.attach_type.id,
            'title': 'My ID',
            'file_data': 'base64data',
            'file_name': 'id.png',
            'file_type': 'image/png',
        }
        form = AttachForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_title(self):
        data = {
            'attach_type': self.attach_type.id,
            'title': '',
            'file_data': 'base64data',
            'file_name': 'id.png',
            'file_type': 'image/png',
        }
        form = AttachForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


class AccountAttachFormTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course, student=self.student, code=1
        )
        self.attach_type = AttachType.objects.create(name='ID Card', code='ID001')
        self.attach = Attach.objects.create(
            attach_type=self.attach_type,
            person=self.user,
            title='My ID',
            file_data='data',
            file_name='id.png',
            file_type='image/png',
        )

    def test_valid_form(self):
        data = {'account': self.account.id, 'attach': self.attach.id}
        form = AccountAttachForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_account(self):
        data = {'account': '', 'attach': self.attach.id}
        form = AccountAttachForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('account', form.errors)


class AccountConditionFormTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course, student=self.student, code=1
        )

    def test_valid_form(self):
        data = {
            'account': self.account.id,
            'title': 'Proof',
            'content': 'Submit proof',
            'fulfilled': False,
        }
        form = AccountConditionForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_title(self):
        data = {'account': self.account.id, 'title': '', 'content': 'Submit proof'}
        form = AccountConditionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


class AccountNoteFormTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course, student=self.student, code=1
        )

    def test_valid_form(self):
        data = {'account': self.account.id, 'content': 'Note content'}
        form = AccountNoteForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_content(self):
        data = {'account': self.account.id, 'content': ''}
        form = AccountNoteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)


class AccountViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course,
            student=self.student,
            code=1,
        )

    def test_list_get_authenticated(self):
        response = self.client.get(reverse('registration-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_search(self):
        response = self.client.get(reverse('registration-list'), {'search': 'Ali'})
        self.assertEqual(response.status_code, 200)

    def test_list_filter_course(self):
        response = self.client.get(reverse('registration-list'), {'course': self.course.id})
        self.assertEqual(response.status_code, 200)

    def test_list_filter_student(self):
        response = self.client.get(reverse('registration-list'), {'student': self.student.id})
        self.assertEqual(response.status_code, 200)

    def test_list_filter_payment_type(self):
        response = self.client.get(reverse('registration-list'), {'payment_type': Account.PAYMENT_TYPE_CASH})
        self.assertEqual(response.status_code, 200)

    def test_detail_get_authenticated(self):
        response = self.client.get(reverse('registration-detail', kwargs={'slug': self.account.slug}))
        self.assertEqual(response.status_code, 200)

    def test_create_get_authenticated(self):
        response = self.client.get(reverse('registration-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_authenticated(self):
        data = {
            'course': self.course.id,
            'student': self.student.id,
            'code': 99,
            'register_date': '2024-01-01T10:00',
            'course_payment_type': Account.PAYMENT_TYPE_CASH,
            'course_price': '1000.00',
            'course_discount_amount': '0.00',
            'course_profit_amount': '0.00',
            'course_credit_amount': '0.00',
            'note': '',
        }
        response = self.client.post(reverse('registration-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Account.objects.filter(code=99).exists())

    def test_update_get_authenticated(self):
        response = self.client.get(reverse('registration-update', kwargs={'slug': self.account.slug}))
        self.assertEqual(response.status_code, 200)

    def test_update_post_authenticated(self):
        data = {
            'course': self.course.id,
            'student': self.student.id,
            'code': 88,
            'register_date': '2024-01-01T10:00',
            'course_payment_type': Account.PAYMENT_TYPE_INSTALLMENT,
            'course_price': '2000.00',
            'course_discount_amount': '0.00',
            'course_profit_amount': '10.00',
            'course_credit_amount': '0.00',
            'note': 'updated',
        }
        response = self.client.post(reverse('registration-update', kwargs={'slug': self.account.slug}), data)
        self.assertEqual(response.status_code, 302)
        self.account.refresh_from_db()
        self.assertEqual(self.account.code, 88)

    def test_delete_get_authenticated(self):
        response = self.client.get(reverse('registration-delete', kwargs={'slug': self.account.slug}))
        self.assertEqual(response.status_code, 200)

    def test_delete_post_authenticated(self):
        response = self.client.post(reverse('registration-delete', kwargs={'slug': self.account.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Account.objects.filter(pk=self.account.pk).exists())

    def test_login_required_redirect(self):
        self.client.logout()
        urls = [
            reverse('registration-list'),
            reverse('registration-detail', kwargs={'slug': self.account.slug}),
            reverse('registration-create'),
            reverse('registration-update', kwargs={'slug': self.account.slug}),
            reverse('registration-delete', kwargs={'slug': self.account.slug}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)


class AttachTypeViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.attach_type = AttachType.objects.create(name='ID', code='ID01')

    def test_list_get(self):
        response = self.client.get(reverse('attachtype-list'))
        self.assertEqual(response.status_code, 200)

    def test_detail_get(self):
        response = self.client.get(reverse('attachtype-detail', kwargs={'pk': self.attach_type.pk}))
        self.assertEqual(response.status_code, 200)

    def test_create_get(self):
        response = self.client.get(reverse('attachtype-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        data = {'name': 'Passport', 'code': 'PP01', 'description': ''}
        response = self.client.post(reverse('attachtype-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AttachType.objects.filter(code='PP01').exists())

    def test_update_get(self):
        response = self.client.get(reverse('attachtype-update', kwargs={'pk': self.attach_type.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_post(self):
        data = {'name': 'ID Updated', 'code': 'ID01', 'description': ''}
        response = self.client.post(reverse('attachtype-update', kwargs={'pk': self.attach_type.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.attach_type.refresh_from_db()
        self.assertEqual(self.attach_type.name, 'ID Updated')

    def test_delete_get(self):
        response = self.client.get(reverse('attachtype-delete', kwargs={'pk': self.attach_type.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        response = self.client.post(reverse('attachtype-delete', kwargs={'pk': self.attach_type.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AttachType.objects.filter(pk=self.attach_type.pk).exists())

    def test_login_required_redirect(self):
        self.client.logout()
        for url_name, kwargs in [
            ('attachtype-list', {}),
            ('attachtype-detail', {'pk': self.attach_type.pk}),
            ('attachtype-create', {}),
            ('attachtype-update', {'pk': self.attach_type.pk}),
            ('attachtype-delete', {'pk': self.attach_type.pk}),
        ]:
            response = self.client.get(reverse(url_name, kwargs=kwargs))
            self.assertEqual(response.status_code, 302, f"Failed for {url_name}")


class AttachViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.attach_type = AttachType.objects.create(name='ID', code='ID01')
        self.attach = Attach.objects.create(
            attach_type=self.attach_type,
            person=self.user,
            title='Doc',
            file_data='data',
            file_name='doc.pdf',
            file_type='application/pdf',
        )

    def test_list_get(self):
        response = self.client.get(reverse('attach-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_filter_type(self):
        response = self.client.get(reverse('attach-list'), {'type': self.attach_type.id})
        self.assertEqual(response.status_code, 200)

    def test_detail_get(self):
        response = self.client.get(reverse('attach-detail', kwargs={'pk': self.attach.pk}))
        self.assertEqual(response.status_code, 200)

    def test_create_get(self):
        response = self.client.get(reverse('attach-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        data = {
            'attach_type': self.attach_type.id,
            'title': 'New Doc',
            'file_data': 'data2',
            'file_name': 'new.pdf',
            'file_type': 'application/pdf',
        }
        response = self.client.post(reverse('attach-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Attach.objects.filter(title='New Doc').exists())

    def test_update_get(self):
        response = self.client.get(reverse('attach-update', kwargs={'pk': self.attach.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_post(self):
        data = {
            'attach_type': self.attach_type.id,
            'title': 'Updated Doc',
            'file_data': 'data',
            'file_name': 'doc.pdf',
            'file_type': 'application/pdf',
        }
        response = self.client.post(reverse('attach-update', kwargs={'pk': self.attach.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.attach.refresh_from_db()
        self.assertEqual(self.attach.title, 'Updated Doc')

    def test_delete_get(self):
        response = self.client.get(reverse('attach-delete', kwargs={'pk': self.attach.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        response = self.client.post(reverse('attach-delete', kwargs={'pk': self.attach.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Attach.objects.filter(pk=self.attach.pk).exists())

    def test_login_required_redirect(self):
        self.client.logout()
        for url_name, kwargs in [
            ('attach-list', {}),
            ('attach-detail', {'pk': self.attach.pk}),
            ('attach-create', {}),
            ('attach-update', {'pk': self.attach.pk}),
            ('attach-delete', {'pk': self.attach.pk}),
        ]:
            response = self.client.get(reverse(url_name, kwargs=kwargs))
            self.assertEqual(response.status_code, 302, f"Failed for {url_name}")


class AccountAttachViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course, student=self.student, code=1
        )
        self.attach_type = AttachType.objects.create(name='ID', code='ID01')
        self.attach = Attach.objects.create(
            attach_type=self.attach_type,
            person=self.user,
            title='Doc',
            file_data='data',
            file_name='doc.pdf',
            file_type='application/pdf',
        )
        self.account_attach = AccountAttach.objects.create(
            account=self.account,
            attach=self.attach,
        )

    def test_list_get(self):
        response = self.client.get(reverse('accountattach-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_filter_account(self):
        response = self.client.get(reverse('accountattach-list'), {'account': self.account.id})
        self.assertEqual(response.status_code, 200)

    def test_detail_get(self):
        response = self.client.get(reverse('accountattach-detail', kwargs={'pk': self.account_attach.pk}))
        self.assertEqual(response.status_code, 200)

    def test_create_get(self):
        response = self.client.get(reverse('accountattach-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        attach2 = Attach.objects.create(
            attach_type=self.attach_type,
            person=self.user,
            title='Doc2',
            file_data='data',
            file_name='doc2.pdf',
            file_type='application/pdf',
        )
        data = {'account': self.account.id, 'attach': attach2.id}
        response = self.client.post(reverse('accountattach-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AccountAttach.objects.filter(attach=attach2).exists())

    def test_update_get(self):
        response = self.client.get(reverse('accountattach-update', kwargs={'pk': self.account_attach.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_post(self):
        attach2 = Attach.objects.create(
            attach_type=self.attach_type,
            person=self.user,
            title='Doc2',
            file_data='data',
            file_name='doc2.pdf',
            file_type='application/pdf',
        )
        data = {'account': self.account.id, 'attach': attach2.id}
        response = self.client.post(reverse('accountattach-update', kwargs={'pk': self.account_attach.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.account_attach.refresh_from_db()
        self.assertEqual(self.account_attach.attach, attach2)

    def test_delete_get(self):
        response = self.client.get(reverse('accountattach-delete', kwargs={'pk': self.account_attach.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        response = self.client.post(reverse('accountattach-delete', kwargs={'pk': self.account_attach.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AccountAttach.objects.filter(pk=self.account_attach.pk).exists())

    def test_login_required_redirect(self):
        self.client.logout()
        for url_name, kwargs in [
            ('accountattach-list', {}),
            ('accountattach-detail', {'pk': self.account_attach.pk}),
            ('accountattach-create', {}),
            ('accountattach-update', {'pk': self.account_attach.pk}),
            ('accountattach-delete', {'pk': self.account_attach.pk}),
        ]:
            response = self.client.get(reverse(url_name, kwargs=kwargs))
            self.assertEqual(response.status_code, 302, f"Failed for {url_name}")


class AccountConditionViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course, student=self.student, code=1
        )
        self.condition = AccountCondition.objects.create(
            account=self.account,
            person=self.user,
            title='Condition',
            content='Content',
        )

    def test_list_get(self):
        response = self.client.get(reverse('accountcondition-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_filter_account(self):
        response = self.client.get(reverse('accountcondition-list'), {'account': self.account.id})
        self.assertEqual(response.status_code, 200)

    def test_list_filter_fulfilled(self):
        response = self.client.get(reverse('accountcondition-list'), {'fulfilled': 'true'})
        self.assertEqual(response.status_code, 200)

    def test_detail_get(self):
        response = self.client.get(reverse('accountcondition-detail', kwargs={'pk': self.condition.pk}))
        self.assertEqual(response.status_code, 200)

    def test_create_get(self):
        response = self.client.get(reverse('accountcondition-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        data = {
            'account': self.account.id,
            'title': 'New Condition',
            'content': 'New Content',
            'fulfilled': False,
        }
        response = self.client.post(reverse('accountcondition-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AccountCondition.objects.filter(title='New Condition').exists())

    def test_update_get(self):
        response = self.client.get(reverse('accountcondition-update', kwargs={'pk': self.condition.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_post(self):
        data = {
            'account': self.account.id,
            'title': 'Updated Condition',
            'content': 'Updated Content',
            'fulfilled': True,
        }
        response = self.client.post(reverse('accountcondition-update', kwargs={'pk': self.condition.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.condition.refresh_from_db()
        self.assertEqual(self.condition.title, 'Updated Condition')
        self.assertTrue(self.condition.fulfilled)

    def test_delete_get(self):
        response = self.client.get(reverse('accountcondition-delete', kwargs={'pk': self.condition.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        response = self.client.post(reverse('accountcondition-delete', kwargs={'pk': self.condition.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AccountCondition.objects.filter(pk=self.condition.pk).exists())

    def test_login_required_redirect(self):
        self.client.logout()
        for url_name, kwargs in [
            ('accountcondition-list', {}),
            ('accountcondition-detail', {'pk': self.condition.pk}),
            ('accountcondition-create', {}),
            ('accountcondition-update', {'pk': self.condition.pk}),
            ('accountcondition-delete', {'pk': self.condition.pk}),
        ]:
            response = self.client.get(reverse(url_name, kwargs=kwargs))
            self.assertEqual(response.status_code, 302, f"Failed for {url_name}")


class AccountNoteViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = Account.objects.create(
            course=self.course, student=self.student, code=1
        )
        self.note = AccountNote.objects.create(
            account=self.account,
            person=self.user,
            content='Note content',
        )

    def test_list_get(self):
        response = self.client.get(reverse('accountnote-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_filter_account(self):
        response = self.client.get(reverse('accountnote-list'), {'account': self.account.id})
        self.assertEqual(response.status_code, 200)

    def test_detail_get(self):
        response = self.client.get(reverse('accountnote-detail', kwargs={'pk': self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_create_get(self):
        response = self.client.get(reverse('accountnote-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        data = {'account': self.account.id, 'content': 'New note content'}
        response = self.client.post(reverse('accountnote-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AccountNote.objects.filter(content='New note content').exists())

    def test_update_get(self):
        response = self.client.get(reverse('accountnote-update', kwargs={'pk': self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_post(self):
        data = {'account': self.account.id, 'content': 'Updated note content'}
        response = self.client.post(reverse('accountnote-update', kwargs={'pk': self.note.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.note.refresh_from_db()
        self.assertEqual(self.note.content, 'Updated note content')

    def test_delete_get(self):
        response = self.client.get(reverse('accountnote-delete', kwargs={'pk': self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_post(self):
        response = self.client.post(reverse('accountnote-delete', kwargs={'pk': self.note.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AccountNote.objects.filter(pk=self.note.pk).exists())

    def test_login_required_redirect(self):
        self.client.logout()
        for url_name, kwargs in [
            ('accountnote-list', {}),
            ('accountnote-detail', {'pk': self.note.pk}),
            ('accountnote-create', {}),
            ('accountnote-update', {'pk': self.note.pk}),
            ('accountnote-delete', {'pk': self.note.pk}),
        ]:
            response = self.client.get(reverse(url_name, kwargs=kwargs))
            self.assertEqual(response.status_code, 302, f"Failed for {url_name}")
