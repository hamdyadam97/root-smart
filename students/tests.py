from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from core.models import Company, Branch
from .models import Contact, Student
from .forms import StudentForm

User = get_user_model()


# ============================================================
# Model Tests
# ============================================================

class ContactModelTest(TestCase):
    def setUp(self):
        self.contact = Contact.objects.create(
            first_name='محمد',
            forth_name='أحمد',
            mobile='0501234567',
            identity_number='1234567890'
        )

    def test_contact_creation(self):
        self.assertEqual(self.contact.first_name, 'محمد')
        self.assertEqual(self.contact.get_full_name(), 'محمد أحمد')
        self.assertEqual(str(self.contact), 'محمد أحمد')

    def test_contact_unique_identity(self):
        # Contact لا يوجد به unique constraint على identity_number
        # لكن يمكننا اختبار إنشاء contact آخر
        contact2 = Contact.objects.create(
            first_name='علي',
            forth_name='خالد',
            mobile='0509876543',
            identity_number='0987654321'
        )
        self.assertEqual(contact2.first_name, 'علي')

    def test_contact_get_short_name(self):
        self.assertEqual(self.contact.get_short_name(), 'محمد أحمد')

    def test_contact_full_name_with_all_names(self):
        contact = Contact.objects.create(
            first_name='أحمد',
            second_name='محمد',
            third_name='علي',
            forth_name='خالد',
            mobile='0501111111'
        )
        self.assertEqual(contact.get_full_name(), 'أحمد محمد علي خالد')


class StudentModelTest(TestCase):
    def setUp(self):
        self.contact = Contact.objects.create(
            first_name='محمد',
            forth_name='أحمد',
            mobile='0501234567',
            identity_number='1234567890'
        )
        self.student = Student.objects.create(
            contact=self.contact,
            level='مبتدئ',
            preferred_contact='whatsapp'
        )

    def test_student_creation(self):
        self.assertEqual(self.student.level, 'مبتدئ')
        self.assertEqual(self.student.get_full_name(), 'محمد أحمد')
        self.assertEqual(str(self.student), 'محمد أحمد')

    def test_student_get_mobile(self):
        self.assertEqual(self.student.get_mobile(), '0501234567')

    def test_student_default_level(self):
        contact = Contact.objects.create(
            first_name='علي',
            forth_name='خالد',
            mobile='0509876543'
        )
        student = Student.objects.create(contact=contact)
        self.assertEqual(student.level, 'مبتدئ')

    def test_student_default_preferred_contact(self):
        contact = Contact.objects.create(
            first_name='علي',
            forth_name='خالد',
            mobile='0509876543'
        )
        student = Student.objects.create(contact=contact)
        self.assertEqual(student.preferred_contact, 'whatsapp')


# ============================================================
# Model Edge Case Tests
# ============================================================

class ContactModelEdgeCaseTest(TestCase):
    def test_contact_blank_names(self):
        contact = Contact.objects.create(
            first_name='أحمد',
            second_name='',
            third_name='',
            forth_name=''
        )
        self.assertEqual(contact.get_full_name(), 'أحمد')
        self.assertEqual(contact.get_short_name(), 'أحمد')

    def test_contact_blank_mobile(self):
        contact = Contact.objects.create(
            first_name='محمد',
            forth_name='أحمد',
            mobile=''
        )
        self.assertEqual(contact.mobile, '')

    def test_contact_all_optional_blank(self):
        contact = Contact.objects.create(
            first_name='علي',
            forth_name='خالد'
        )
        self.assertEqual(contact.address, '')
        self.assertEqual(contact.nationality, '')
        self.assertEqual(contact.identity_number, '')
        self.assertIsNone(contact.birth_date)
        self.assertIsNone(contact.identity_start_date)


class StudentModelEdgeCaseTest(TestCase):
    def test_student_cascade_delete_contact(self):
        contact = Contact.objects.create(
            first_name='محمد',
            forth_name='أحمد',
            mobile='0501234567'
        )
        student = Student.objects.create(contact=contact)
        student_pk = student.pk
        contact.delete()
        self.assertFalse(Student.objects.filter(pk=student_pk).exists())

    def test_student_level_choices(self):
        contact = Contact.objects.create(first_name='أحمد', forth_name='خالد')
        for level in ['مبتدئ', 'متوسط', 'متقدم']:
            with self.subTest(level=level):
                c = Contact.objects.create(first_name=f'ت{level}', forth_name='ت')
                student = Student.objects.create(contact=c, level=level)
                self.assertEqual(student.level, level)

    def test_student_preferred_contact_choices(self):
        contact = Contact.objects.create(first_name='أحمد', forth_name='خالد')
        for method in ['email', 'whatsapp', 'app']:
            with self.subTest(method=method):
                c = Contact.objects.create(first_name=f'ت{method}', forth_name='ت')
                student = Student.objects.create(contact=c, preferred_contact=method)
                self.assertEqual(student.preferred_contact, method)


# ============================================================
# Form Tests
# ============================================================

class StudentFormTest(TestCase):
    def test_valid_student_form(self):
        data = {
            'first_name': 'محمد',
            'forth_name': 'أحمد',
            'mobile': '0501234567',
            'level': 'مبتدئ',
            'preferred_contact': 'whatsapp',
        }
        form = StudentForm(data=data)
        self.assertTrue(form.is_valid())

    def test_valid_student_form_with_optional_fields(self):
        data = {
            'first_name': 'محمد',
            'second_name': 'علي',
            'third_name': 'خالد',
            'forth_name': 'أحمد',
            'address': 'الرياض',
            'mobile': '0501234567',
            'phone': '0111234567',
            'nationality': 'سعودي',
            'identity_number': '1234567890',
            'identity_location': 'الرياض',
            'identity_start_date': '2020-01-01',
            'birth_date': '1990-01-01',
            'birth_location': 'جدة',
            'qualification': 'بكالوريوس',
            'photo': '',
            'level': 'متوسط',
            'preferred_contact': 'email',
        }
        form = StudentForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_student_form_missing_first_name(self):
        data = {
            'first_name': '',
            'forth_name': 'أحمد',
            'level': 'مبتدئ',
            'preferred_contact': 'whatsapp',
        }
        form = StudentForm(data=data)
        self.assertFalse(form.is_valid())

    def test_invalid_student_form_missing_forth_name(self):
        data = {
            'first_name': 'محمد',
            'forth_name': '',
            'level': 'مبتدئ',
            'preferred_contact': 'whatsapp',
        }
        form = StudentForm(data=data)
        self.assertFalse(form.is_valid())

    def test_student_form_init_with_instance(self):
        contact = Contact.objects.create(
            first_name='محمد',
            second_name='علي',
            third_name='خالد',
            forth_name='أحمد',
            address='الرياض',
            mobile='0501234567',
            phone='0111234567',
            nationality='سعودي',
            identity_number='1234567890',
            identity_location='الرياض',
            identity_start_date='2020-01-01',
            birth_date='1990-01-01',
            birth_location='جدة',
            qualification='بكالوريوس',
            photo='data:image/png;base64,abc',
        )
        student = Student.objects.create(contact=contact, level='متقدم', preferred_contact='app')
        form = StudentForm(instance=student)
        self.assertEqual(form.fields['first_name'].initial, 'محمد')
        self.assertEqual(form.fields['second_name'].initial, 'علي')
        self.assertEqual(form.fields['third_name'].initial, 'خالد')
        self.assertEqual(form.fields['forth_name'].initial, 'أحمد')
        self.assertEqual(form.fields['address'].initial, 'الرياض')
        self.assertEqual(form.fields['mobile'].initial, '0501234567')
        self.assertEqual(form.fields['phone'].initial, '0111234567')
        self.assertEqual(form.fields['nationality'].initial, 'سعودي')
        self.assertEqual(form.fields['identity_number'].initial, '1234567890')
        self.assertEqual(form.fields['identity_location'].initial, 'الرياض')
        self.assertEqual(form.fields['identity_start_date'].initial, '2020-01-01')
        self.assertEqual(form.fields['birth_date'].initial, '1990-01-01')
        self.assertEqual(form.fields['birth_location'].initial, 'جدة')
        self.assertEqual(form.fields['qualification'].initial, 'بكالوريوس')
        self.assertEqual(form.fields['photo'].initial.name if hasattr(form.fields['photo'].initial, 'name') else form.fields['photo'].initial, 'data:image/png;base64,abc')


# ============================================================
# View Tests
# ============================================================

class StudentViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            forth_name='User',
            is_staff=True
        )
        self.client.force_login(self.user)
        self.contact = Contact.objects.create(
            first_name='محمد',
            forth_name='أحمد',
            mobile='0501234567',
            identity_number='1234567890'
        )
        self.student = Student.objects.create(
            contact=self.contact,
            level='مبتدئ',
            preferred_contact='whatsapp'
        )
        self.contact2 = Contact.objects.create(
            first_name='علي',
            forth_name='خالد',
            mobile='0509876543',
            identity_number='0987654321'
        )
        self.student2 = Student.objects.create(
            contact=self.contact2,
            level='متوسط',
            preferred_contact='email'
        )

    def test_student_list_get(self):
        response = self.client.get(reverse('student-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'محمد أحمد')
        self.assertContains(response, 'علي خالد')

    def test_student_list_search_by_first_name(self):
        response = self.client.get(reverse('student-list'), {'search': 'محمد'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'محمد أحمد')

    def test_student_list_search_by_forth_name(self):
        response = self.client.get(reverse('student-list'), {'search': 'خالد'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'علي خالد')

    def test_student_list_search_by_mobile(self):
        response = self.client.get(reverse('student-list'), {'search': '0509876543'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'علي خالد')

    def test_student_list_filter_by_level(self):
        response = self.client.get(reverse('student-list'), {'level': 'مبتدئ'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'محمد أحمد')

    def test_student_list_filter_by_preferred_contact(self):
        response = self.client.get(reverse('student-list'), {'preferred_contact': 'email'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'علي خالد')

    def test_student_detail_get(self):
        response = self.client.get(reverse('student-detail', kwargs={'pk': self.student.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'محمد أحمد')

    def test_student_create_get(self):
        response = self.client.get(reverse('student-create'))
        self.assertEqual(response.status_code, 200)

    def test_student_create_post(self):
        data = {
            'first_name': 'خالد',
            'second_name': 'عمر',
            'third_name': '',
            'forth_name': 'سالم',
            'address': 'جدة',
            'mobile': '0501111111',
            'phone': '',
            'nationality': 'سعودي',
            'identity_number': '1111111111',
            'identity_location': 'جدة',
            'identity_start_date': '',
            'birth_date': '',
            'birth_location': '',
            'qualification': '',
            'photo': '',
            'level': 'متقدم',
            'preferred_contact': 'app',
        }
        response = self.client.post(reverse('student-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Student.objects.filter(contact__first_name='خالد', contact__forth_name='سالم').exists())

    def test_student_update_get(self):
        response = self.client.get(reverse('student-update', kwargs={'pk': self.student.pk}))
        self.assertEqual(response.status_code, 200)

    def test_student_update_post(self):
        data = {
            'first_name': 'محمد',
            'second_name': 'علي',
            'third_name': '',
            'forth_name': 'أحمد',
            'address': 'الدمام',
            'mobile': '0501234567',
            'phone': '',
            'nationality': '',
            'identity_number': '1234567890',
            'identity_location': '',
            'identity_start_date': '',
            'birth_date': '',
            'birth_location': '',
            'qualification': '',
            'photo': '',
            'level': 'متوسط',
            'preferred_contact': 'email',
        }
        response = self.client.post(reverse('student-update', kwargs={'pk': self.student.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.contact.refresh_from_db()
        self.assertEqual(self.student.level, 'متوسط')
        self.assertEqual(self.contact.address, 'الدمام')

    def test_student_delete_get(self):
        response = self.client.get(reverse('student-delete', kwargs={'pk': self.student.pk}))
        self.assertEqual(response.status_code, 200)

    def test_student_delete_post(self):
        response = self.client.post(reverse('student-delete', kwargs={'pk': self.student.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Student.objects.filter(pk=self.student.pk).exists())
        # Contact is NOT cascade-deleted when student is deleted (CASCADE is on Student side)
        self.assertTrue(Contact.objects.filter(pk=self.contact.pk).exists())

    def test_student_views_login_required(self):
        self.client.logout()
        urls = [
            reverse('student-list'),
            reverse('student-detail', kwargs={'pk': self.student.pk}),
            reverse('student-create'),
            reverse('student-update', kwargs={'pk': self.student.pk}),
            reverse('student-delete', kwargs={'pk': self.student.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))


# ============================================================
# View Edge Case Tests
# ============================================================

class StudentViewEdgeCaseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            first_name='Test',
            forth_name='User',
            is_staff=True
        )
        self.client.force_login(self.user)
        self.contact = Contact.objects.create(
            first_name='محمد',
            forth_name='أحمد',
            mobile='0501234567',
        )
        self.student = Student.objects.create(
            contact=self.contact,
            level='مبتدئ',
            preferred_contact='whatsapp'
        )
        self.contact2 = Contact.objects.create(
            first_name='علي',
            forth_name='خالد',
            mobile='0509876543',
        )
        self.student2 = Student.objects.create(
            contact=self.contact2,
            level='متوسط',
            preferred_contact='email'
        )

    def test_student_list_search_no_results(self):
        response = self.client.get(reverse('student-list'), {'search': 'nonexistentxyz'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'محمد أحمد')
        self.assertNotContains(response, 'علي خالد')

    def test_student_list_combined_filters(self):
        response = self.client.get(
            reverse('student-list'),
            {'level': 'مبتدئ', 'preferred_contact': 'whatsapp'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'محمد أحمد')
        self.assertNotContains(response, 'علي خالد')

    def test_student_list_filter_no_results(self):
        response = self.client.get(
            reverse('student-list'),
            {'level': 'متقدم', 'preferred_contact': 'app'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'محمد أحمد')
        self.assertNotContains(response, 'علي خالد')

    def test_student_create_post_invalid_missing_first_name(self):
        data = {
            'first_name': '',
            'forth_name': 'أحمد',
            'mobile': '0501234567',
            'level': 'مبتدئ',
            'preferred_contact': 'whatsapp',
        }
        response = self.client.post(reverse('student-create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Student.objects.filter(contact__forth_name='أحمد', contact__first_name='').exists())

    def test_student_create_post_anonymous(self):
        self.client.logout()
        data = {
            'first_name': 'Anon',
            'forth_name': 'User',
            'level': 'مبتدئ',
            'preferred_contact': 'whatsapp',
        }
        response = self.client.post(reverse('student-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_student_update_post_invalid(self):
        data = {
            'first_name': '',
            'forth_name': 'أحمد',
            'level': 'متوسط',
            'preferred_contact': 'email',
        }
        response = self.client.post(reverse('student-update', kwargs={'pk': self.student.pk}), data)
        self.assertEqual(response.status_code, 200)
        self.student.refresh_from_db()
        self.assertEqual(self.student.level, 'مبتدئ')

    def test_student_update_404(self):
        response = self.client.get(reverse('student-update', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_student_delete_404(self):
        response = self.client.get(reverse('student-delete', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_student_detail_404(self):
        response = self.client.get(reverse('student-detail', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, 404)

    def test_redirect_after_create(self):
        data = {
            'first_name': 'Redirect',
            'forth_name': 'Test',
            'mobile': '0500000000',
            'level': 'متقدم',
            'preferred_contact': 'app',
        }
        response = self.client.post(reverse('student-create'), data)
        self.assertRedirects(response, reverse('student-list'))

    def test_redirect_after_update(self):
        data = {
            'first_name': 'محمد',
            'forth_name': 'أحمد',
            'mobile': '0501234567',
            'level': 'متوسط',
            'preferred_contact': 'email',
        }
        response = self.client.post(reverse('student-update', kwargs={'pk': self.student.pk}), data)
        self.assertRedirects(response, reverse('student-list'))

    def test_redirect_after_delete(self):
        response = self.client.post(reverse('student-delete', kwargs={'pk': self.student.pk}))
        self.assertRedirects(response, reverse('student-list'))

    def test_anonymous_post_update_redirects(self):
        self.client.logout()
        data = {
            'first_name': 'محمد',
            'forth_name': 'أحمد',
            'level': 'متوسط',
            'preferred_contact': 'email',
        }
        response = self.client.post(reverse('student-update', kwargs={'pk': self.student.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_anonymous_post_delete_redirects(self):
        self.client.logout()
        response = self.client.post(reverse('student-delete', kwargs={'pk': self.student.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))
