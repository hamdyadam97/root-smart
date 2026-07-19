from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import AppNotification

User = get_user_model()


class AppNotificationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='t@t.com', password='123', first_name='A', forth_name='B'
        )

    def test_create_app_notification(self):
        notif = AppNotification.objects.create(
            user=self.user,
            title='Test Title',
            body='Test Body',
            notification_type='تنبيه',
            action_url='/test/',
        )
        self.assertEqual(notif.title, 'Test Title')
        self.assertEqual(notif.body, 'Test Body')
        self.assertEqual(notif.notification_type, 'تنبيه')
        self.assertFalse(notif.is_read)
        self.assertEqual(notif.action_url, '/test/')
        self.assertEqual(notif.user, self.user)

    def test_str_method(self):
        notif = AppNotification.objects.create(
            user=self.user,
            title='Hello',
            body='World',
            notification_type='رسالة',
        )
        expected = f"{self.user.get_short_name()} - Hello"
        self.assertEqual(str(notif), expected)

    def test_notification_type_choices_validation(self):
        valid_choices = [choice[0] for choice in AppNotification.TYPE_CHOICES]
        for choice in valid_choices:
            notif = AppNotification.objects.create(
                user=self.user,
                title=f'Test {choice}',
                body='Body',
                notification_type=choice,
            )
            self.assertEqual(notif.notification_type, choice)

    def test_ordering(self):
        notif1 = AppNotification.objects.create(
            user=self.user, title='First', body='Body', notification_type='تقرير'
        )
        notif2 = AppNotification.objects.create(
            user=self.user, title='Second', body='Body', notification_type='عرض_جديد'
        )
        notifs = list(AppNotification.objects.all())
        self.assertEqual(notifs[0], notif2)
        self.assertEqual(notifs[1], notif1)


class AppNotificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='t@t.com', password='123', first_name='A', forth_name='B'
        )
        self.user2 = User.objects.create_user(
            email='t2@t.com', password='123', first_name='C', forth_name='D'
        )
        self.notification = AppNotification.objects.create(
            user=self.user,
            title='Test Title',
            body='Test Body',
            notification_type='تنبيه',
            action_url='/action/',
        )

    def test_list_view_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(reverse('appnotification-list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('notifications', response.context)

    def test_list_view_search(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(reverse('appnotification-list'), {'q': 'Test'})
        self.assertEqual(response.status_code, 200)

    def test_detail_view_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(
            reverse('appnotification-detail', kwargs={'pk': self.notification.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('notification', response.context)

    def test_detail_view_marks_read(self):
        self.client.login(username='t@t.com', password='123')
        self.assertFalse(self.notification.is_read)
        response = self.client.get(
            reverse('appnotification-detail', kwargs={'pk': self.notification.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_create_view_get_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(reverse('appnotification-create'))
        self.assertEqual(response.status_code, 200)

    def test_create_view_post_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        data = {
            'title': 'New Title',
            'body': 'New Body',
            'notification_type': 'رسالة',
            'action_url': '/new/',
        }
        response = self.client.post(reverse('appnotification-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            AppNotification.objects.filter(title='New Title').exists()
        )
        notif = AppNotification.objects.get(title='New Title')
        self.assertEqual(notif.user, self.user)

    def test_update_view_get_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(
            reverse('appnotification-update', kwargs={'pk': self.notification.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_update_view_post_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        data = {
            'title': 'Updated Title',
            'body': 'Updated Body',
            'notification_type': 'عرض_جديد',
            'action_url': '/updated/',
        }
        response = self.client.post(
            reverse('appnotification-update', kwargs={'pk': self.notification.pk}),
            data,
        )
        self.assertEqual(response.status_code, 302)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.title, 'Updated Title')
        self.assertEqual(self.notification.notification_type, 'عرض_جديد')

    def test_delete_view_get_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.get(
            reverse('appnotification-delete', kwargs={'pk': self.notification.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_view_post_authenticated(self):
        self.client.login(username='t@t.com', password='123')
        response = self.client.post(
            reverse('appnotification-delete', kwargs={'pk': self.notification.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            AppNotification.objects.filter(pk=self.notification.pk).exists()
        )

    def test_list_view_redirects_anonymous(self):
        response = self.client.get(reverse('appnotification-list'))
        self.assertEqual(response.status_code, 302)

    def test_detail_view_redirects_anonymous(self):
        response = self.client.get(
            reverse('appnotification-detail', kwargs={'pk': self.notification.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_create_view_redirects_anonymous(self):
        response = self.client.get(reverse('appnotification-create'))
        self.assertEqual(response.status_code, 302)

    def test_update_view_redirects_anonymous(self):
        response = self.client.get(
            reverse('appnotification-update', kwargs={'pk': self.notification.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_delete_view_redirects_anonymous(self):
        response = self.client.get(
            reverse('appnotification-delete', kwargs={'pk': self.notification.pk})
        )
        self.assertEqual(response.status_code, 302)
