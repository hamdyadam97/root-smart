from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import InternalMessage

User = get_user_model()


class InternalMessageModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='t@t.com', password='123', first_name='A', forth_name='B'
        )
        self.user2 = User.objects.create_user(
            email='t2@t.com', password='123', first_name='C', forth_name='D'
        )

    def test_create_internal_message(self):
        msg = InternalMessage.objects.create(
            sender=self.user,
            recipient=self.user2,
            subject='Test Subject',
            body='Test Body',
            message_type='استفسار',
        )
        self.assertEqual(msg.subject, 'Test Subject')
        self.assertEqual(msg.body, 'Test Body')
        self.assertEqual(msg.message_type, 'استفسار')
        self.assertFalse(msg.is_read)
        self.assertEqual(msg.sender, self.user)
        self.assertEqual(msg.recipient, self.user2)

    def test_str_method(self):
        msg = InternalMessage.objects.create(
            sender=self.user,
            recipient=self.user2,
            subject='Hello',
            body='World',
        )
        expected = f"من {self.user.get_short_name()} إلى {self.user2.get_short_name()}: Hello"
        self.assertEqual(str(msg), expected)

    def test_message_type_choices_validation(self):
        valid_choices = [choice[0] for choice in InternalMessage.TYPE_CHOICES]
        for choice in valid_choices:
            msg = InternalMessage.objects.create(
                sender=self.user,
                recipient=self.user2,
                subject=f'Test {choice}',
                body='Body',
                message_type=choice,
            )
            self.assertEqual(msg.message_type, choice)

    def test_sender_and_recipient_are_different(self):
        msg = InternalMessage.objects.create(
            sender=self.user,
            recipient=self.user2,
            subject='Different',
            body='Users',
        )
        self.assertNotEqual(msg.sender, msg.recipient)

    def test_ordering(self):
        msg1 = InternalMessage.objects.create(
            sender=self.user, recipient=self.user2, subject='First', body='Body'
        )
        msg2 = InternalMessage.objects.create(
            sender=self.user2, recipient=self.user, subject='Second', body='Body'
        )
        msgs = list(InternalMessage.objects.all())
        self.assertEqual(msgs[0], msg2)
        self.assertEqual(msgs[1], msg1)


class InternalMessageViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='t@t.com', password='123', first_name='A', forth_name='B'
        )
        self.user2 = User.objects.create_user(
            email='t2@t.com', password='123', first_name='C', forth_name='D'
        )
        self.message = InternalMessage.objects.create(
            sender=self.user,
            recipient=self.user2,
            subject='Test Subject',
            body='Test Body',
            message_type='ملاحظة',
        )

    def test_list_view_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(reverse('internalmessage-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('messages_list', response.context)

    def test_list_view_search(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(reverse('internalmessage-list'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)

    def test_detail_view_authenticated_sender(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(
            reverse('internalmessage-detail', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('message_obj', response.context)

    def test_detail_view_authenticated_recipient_marks_read(self):
        self.client.login(username='t2@t.com', password='123')
        self.assertFalse(self.message.is_read)
        response = self.client.get(
            reverse('internalmessage-detail', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_read)

    def test_create_view_get_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(reverse('internalmessage-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_view_post_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        data = {
            'recipient': self.user2.pk,
            'subject': 'New Subject',
            'body': 'New Body',
            'message_type': 'عام',
        }
        response = self.client.post(reverse('internalmessage-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            InternalMessage.objects.filter(subject='New Subject').exists()
        )
        msg = InternalMessage.objects.get(subject='New Subject')
        self.assertEqual(msg.sender, self.user)

    def test_update_view_get_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(
            reverse('internalmessage-update', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_update_view_post_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        data = {
            'recipient': self.user2.pk,
            'subject': 'Updated Subject',
            'body': 'Updated Body',
            'message_type': 'طلب_دعم',
        }
        response = self.client.post(
            reverse('internalmessage-update', kwargs={'pk': self.message.pk}), data
        )
        self.assertEqual(response.status_code, 302)
        self.message.refresh_from_db()
        self.assertEqual(self.message.subject, 'Updated Subject')
        self.assertEqual(self.message.message_type, 'طلب_دعم')

    def test_delete_view_get_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(
            reverse('internalmessage-delete', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_view_post_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.post(
            reverse('internalmessage-delete', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            InternalMessage.objects.filter(pk=self.message.pk).exists()
        )

    def test_list_view_redirects_anonymous(self):
        response = self.client.get(reverse('internalmessage-list'))
        self.assertEqual(response.status_code, 302)

    def test_detail_view_redirects_anonymous(self):
        response = self.client.get(
            reverse('internalmessage-detail', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_create_view_redirects_anonymous(self):
        response = self.client.get(reverse('internalmessage-create'))
        self.assertEqual(response.status_code, 302)

    def test_update_view_redirects_anonymous(self):
        response = self.client.get(
            reverse('internalmessage-update', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_view_redirects_anonymous(self):
        response = self.client.get(
            reverse('internalmessage-delete', kwargs={'pk': self.message.pk})
        )
        self.assertEqual(response.status_code, 302)
