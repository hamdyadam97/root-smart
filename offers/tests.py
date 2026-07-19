from django.db.models import ProtectedError
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Company, Branch
from courses.models import Master, Course
from students.models import Contact, Student

from .models import StudentOffer, OfferRecipient, OfferNote
from .forms import StudentOfferForm, OfferRecipientForm, OfferNoteForm


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


class StudentOfferModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.offer = StudentOffer.objects.create(
            title='Summer Offer',
            content='Great discount',
            branch=self.branch,
            course=self.course,
            status='مسودة',
            created_by=self.user,
        )

    def test_creation_and_str(self):
        self.assertEqual(str(self.offer), 'Summer Offer')
        self.assertEqual(self.offer.status, 'مسودة')
        self.assertIsNone(self.offer.sent_at)

    def test_send_now_sets_status_and_sent_at(self):
        self.offer.send_now()
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.status, 'مرسلة')
        self.assertIsNotNone(self.offer.sent_at)
        self.assertLessEqual((timezone.now() - self.offer.sent_at).total_seconds(), 5)

    def test_branch_protect(self):
        with self.assertRaises(ProtectedError):
            self.branch.delete()

    def test_course_set_null(self):
        self.course.delete()
        self.offer.refresh_from_db()
        self.assertIsNone(self.offer.course)


class OfferRecipientModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.offer = StudentOffer.objects.create(
            title='Summer Offer',
            content='Great discount',
            branch=self.branch,
            created_by=self.user,
        )
        self.recipient = OfferRecipient.objects.create(
            offer=self.offer,
            student=self.student,
            channel='email',
            status='مرسل',
        )

    def test_creation_and_str(self):
        expected = f"{self.student.get_full_name()} - {self.offer.title}"
        self.assertEqual(str(self.recipient), expected)

    def test_unique_together(self):
        with self.assertRaises(Exception):
            OfferRecipient.objects.create(
                offer=self.offer,
                student=self.student,
                channel='email',
            )

    def test_offer_cascade(self):
        # After changing on_delete to CASCADE, deleting offer deletes recipients
        recipient_pk = self.recipient.pk
        self.offer.delete()
        self.assertFalse(OfferRecipient.objects.filter(pk=recipient_pk).exists())

    def test_student_protect(self):
        with self.assertRaises(ProtectedError):
            self.student.delete()


class OfferNoteModelTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.offer = StudentOffer.objects.create(
            title='Summer Offer',
            content='Great discount',
            branch=self.branch,
            created_by=self.user,
        )
        self.note = OfferNote.objects.create(
            offer=self.offer,
            person=self.user,
            note_text='Follow up needed',
        )

    def test_creation_and_str(self):
        expected = f"{self.user.get_short_name()} - {self.offer.title}"
        self.assertEqual(str(self.note), expected)


class StudentOfferFormTests(BaseTestCase):
    def test_valid_form(self):
        data = {
            'title': 'New Offer',
            'content': 'Offer content',
            'branch': self.branch.id,
            'course': self.course.id,
            'status': 'مسودة',
        }
        form = StudentOfferForm(data=data)
        self.assertTrue(form.is_valid())

    def test_valid_form_without_course(self):
        data = {
            'title': 'New Offer',
            'content': 'Offer content',
            'branch': self.branch.id,
            'course': '',
            'status': 'مجدولة',
            'scheduled_at': '2024-12-01T10:00',
        }
        form = StudentOfferForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_title(self):
        data = {
            'title': '',
            'content': 'Offer content',
            'branch': self.branch.id,
        }
        form = StudentOfferForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

    def test_invalid_missing_branch(self):
        data = {
            'title': 'New Offer',
            'content': 'Offer content',
            'branch': '',
        }
        form = StudentOfferForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('branch', form.errors)


class OfferRecipientFormTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.offer = StudentOffer.objects.create(
            title='Summer Offer',
            content='Great discount',
            branch=self.branch,
            created_by=self.user,
        )

    def test_valid_form(self):
        data = {
            'offer': self.offer.id,
            'student': self.student.id,
            'channel': 'whatsapp',
            'status': 'مرسل',
        }
        form = OfferRecipientForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_student(self):
        data = {
            'offer': self.offer.id,
            'student': '',
            'channel': 'email',
        }
        form = OfferRecipientForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('student', form.errors)

    def test_invalid_missing_channel(self):
        data = {
            'offer': self.offer.id,
            'student': self.student.id,
            'channel': '',
        }
        form = OfferRecipientForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('channel', form.errors)


class OfferNoteFormTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.offer = StudentOffer.objects.create(
            title='Summer Offer',
            content='Great discount',
            branch=self.branch,
            created_by=self.user,
        )

    def test_valid_form(self):
        data = {
            'offer': self.offer.id,
            'note_text': 'This is a note',
        }
        form = OfferNoteForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_missing_note_text(self):
        data = {
            'offer': self.offer.id,
            'note_text': '',
        }
        form = OfferNoteForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('note_text', form.errors)


class StudentOfferViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.offer = StudentOffer.objects.create(
            title='Summer Offer',
            content='Great discount',
            branch=self.branch,
            course=self.course,
            created_by=self.user,
        )

    def test_list_get_authenticated(self):
        response = self.client.get(reverse('studentoffer-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_search(self):
        response = self.client.get(reverse('studentoffer-list'), {'q': 'Summer'})
        self.assertEqual(response.status_code, 200)

    def test_detail_get_authenticated(self):
        response = self.client.get(reverse('studentoffer-detail', kwargs={'slug': self.offer.slug}))
        self.assertEqual(response.status_code, 200)

    def test_export_pdf(self):
        from accounts.models import Role, EmployeeRole, Permission
        role = Role.objects.create(name='offer_viewer_test')
        perm = Permission.objects.get(codename='view_studentoffer')
        role.permissions.add(perm)
        EmployeeRole.objects.create(person=self.user, role=role, branch=self.branch)

        response = self.client.get(reverse('studentoffer-export-pdf', kwargs={'slug': self.offer.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(response.content.startswith(b'%PDF'))

    def test_create_get_authenticated(self):
        response = self.client.get(reverse('studentoffer-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_authenticated(self):
        data = {
            'title': 'Winter Offer',
            'content': 'Winter discount',
            'branch': self.branch.id,
            'course': self.course.id,
            'status': 'مسودة',
        }
        response = self.client.post(reverse('studentoffer-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(StudentOffer.objects.filter(title='Winter Offer').exists())

    def test_update_get_authenticated(self):
        response = self.client.get(reverse('studentoffer-update', kwargs={'slug': self.offer.slug}))
        self.assertEqual(response.status_code, 200)

    def test_update_post_authenticated(self):
        data = {
            'title': 'Updated Offer',
            'content': 'Updated discount',
            'branch': self.branch.id,
            'course': self.course.id,
            'status': 'مجدولة',
            'scheduled_at': '2024-12-01T10:00',
        }
        response = self.client.post(reverse('studentoffer-update', kwargs={'slug': self.offer.slug}), data)
        self.assertEqual(response.status_code, 302)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, 'Updated Offer')

    def test_delete_get_authenticated(self):
        response = self.client.get(reverse('studentoffer-delete', kwargs={'slug': self.offer.slug}))
        self.assertEqual(response.status_code, 200)

    def test_delete_post_authenticated(self):
        response = self.client.post(reverse('studentoffer-delete', kwargs={'slug': self.offer.slug}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(StudentOffer.objects.filter(pk=self.offer.pk).exists())

    def test_login_required_redirect(self):
        self.client.logout()
        urls = [
            reverse('studentoffer-list'),
            reverse('studentoffer-detail', kwargs={'slug': self.offer.slug}),
            reverse('studentoffer-create'),
            reverse('studentoffer-update', kwargs={'slug': self.offer.slug}),
            reverse('studentoffer-delete', kwargs={'slug': self.offer.slug}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)


class OfferRecipientViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.offer = StudentOffer.objects.create(
            title='Summer Offer',
            content='Great discount',
            branch=self.branch,
            created_by=self.user,
        )
        self.recipient = OfferRecipient.objects.create(
            offer=self.offer,
            student=self.student,
            channel='email',
            status='مرسل',
        )

    def test_list_get_authenticated(self):
        response = self.client.get(reverse('offerrecipient-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_search(self):
        response = self.client.get(reverse('offerrecipient-list'), {'q': 'Ali'})
        self.assertEqual(response.status_code, 200)

    def test_detail_get_authenticated(self):
        response = self.client.get(reverse('offerrecipient-detail', kwargs={'pk': self.recipient.pk}))
        self.assertEqual(response.status_code, 200)

    def test_create_get_authenticated(self):
        response = self.client.get(reverse('offerrecipient-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_authenticated(self):
        contact2 = Contact.objects.create(first_name='Omar', forth_name='Khaled')
        student2 = Student.objects.create(contact=contact2)
        data = {
            'offer': self.offer.id,
            'student': student2.id,
            'channel': 'whatsapp',
            'status': 'مرسل',
        }
        response = self.client.post(reverse('offerrecipient-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(OfferRecipient.objects.filter(student=student2, channel='whatsapp').exists())

    def test_update_get_authenticated(self):
        response = self.client.get(reverse('offerrecipient-update', kwargs={'pk': self.recipient.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_post_authenticated(self):
        data = {
            'offer': self.offer.id,
            'student': self.student.id,
            'channel': 'email',
            'status': 'مقروء',
        }
        response = self.client.post(reverse('offerrecipient-update', kwargs={'pk': self.recipient.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.recipient.refresh_from_db()
        self.assertEqual(self.recipient.status, 'مقروء')

    def test_delete_get_authenticated(self):
        response = self.client.get(reverse('offerrecipient-delete', kwargs={'pk': self.recipient.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_post_authenticated(self):
        response = self.client.post(reverse('offerrecipient-delete', kwargs={'pk': self.recipient.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(OfferRecipient.objects.filter(pk=self.recipient.pk).exists())

    def test_login_required_redirect(self):
        self.client.logout()
        urls = [
            reverse('offerrecipient-list'),
            reverse('offerrecipient-detail', kwargs={'pk': self.recipient.pk}),
            reverse('offerrecipient-create'),
            reverse('offerrecipient-update', kwargs={'pk': self.recipient.pk}),
            reverse('offerrecipient-delete', kwargs={'pk': self.recipient.pk}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)


class OfferNoteViewTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.offer = StudentOffer.objects.create(
            title='Summer Offer',
            content='Great discount',
            branch=self.branch,
            created_by=self.user,
        )
        self.note = OfferNote.objects.create(
            offer=self.offer,
            person=self.user,
            note_text='Initial note',
        )

    def test_list_get_authenticated(self):
        response = self.client.get(reverse('offernote-list'))
        self.assertEqual(response.status_code, 200)

    def test_list_search(self):
        response = self.client.get(reverse('offernote-list'), {'q': 'Initial'})
        self.assertEqual(response.status_code, 200)

    def test_detail_get_authenticated(self):
        response = self.client.get(reverse('offernote-detail', kwargs={'pk': self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_create_get_authenticated(self):
        response = self.client.get(reverse('offernote-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_authenticated(self):
        data = {
            'offer': self.offer.id,
            'note_text': 'New note text',
        }
        response = self.client.post(reverse('offernote-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(OfferNote.objects.filter(note_text='New note text').exists())

    def test_update_get_authenticated(self):
        response = self.client.get(reverse('offernote-update', kwargs={'pk': self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_update_post_authenticated(self):
        data = {
            'offer': self.offer.id,
            'note_text': 'Updated note text',
        }
        response = self.client.post(reverse('offernote-update', kwargs={'pk': self.note.pk}), data)
        self.assertEqual(response.status_code, 302)
        self.note.refresh_from_db()
        self.assertEqual(self.note.note_text, 'Updated note text')

    def test_delete_get_authenticated(self):
        response = self.client.get(reverse('offernote-delete', kwargs={'pk': self.note.pk}))
        self.assertEqual(response.status_code, 200)

    def test_delete_post_authenticated(self):
        response = self.client.post(reverse('offernote-delete', kwargs={'pk': self.note.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(OfferNote.objects.filter(pk=self.note.pk).exists())

    def test_login_required_redirect(self):
        self.client.logout()
        urls = [
            reverse('offernote-list'),
            reverse('offernote-detail', kwargs={'pk': self.note.pk}),
            reverse('offernote-create'),
            reverse('offernote-update', kwargs={'pk': self.note.pk}),
            reverse('offernote-delete', kwargs={'pk': self.note.pk}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
