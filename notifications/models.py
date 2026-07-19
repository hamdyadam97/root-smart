from django.db import models


class AppNotification(models.Model):
    """إشعارات التطبيق"""
    TYPE_CHOICES = [
        ('عرض_جديد', 'عرض جديد'),
        ('رسالة', 'رسالة'),
        ('تقرير', 'تقرير'),
        ('تنبيه', 'تنبيه'),
    ]

    user = models.ForeignKey('accounts.Person', on_delete=models.CASCADE, db_index=True, related_name='app_notifications', verbose_name='المستخدم')
    title = models.CharField(max_length=255, db_index=True, verbose_name='العنوان')
    body = models.TextField(verbose_name='المحتوى')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True, verbose_name='نوع الإشعار')
    is_read = models.BooleanField(default=False, db_index=True, verbose_name='مقروء')
    action_url = models.CharField(max_length=255, blank=True, verbose_name='رابط الإجراء')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_short_name()} - {self.title}"
