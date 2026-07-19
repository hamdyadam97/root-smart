from django.db import models


class InternalMessage(models.Model):
    """التواصل الداخلي"""
    TYPE_CHOICES = [
        ('استفسار', 'استفسار'),
        ('ملاحظة', 'ملاحظة'),
        ('طلب_دعم', 'طلب دعم'),
        ('عام', 'عام'),
    ]

    sender = models.ForeignKey('accounts.Person', on_delete=models.CASCADE, db_index=True, related_name='sent_messages', verbose_name='المرسل')
    recipient = models.ForeignKey('accounts.Person', on_delete=models.CASCADE, db_index=True, related_name='received_messages', verbose_name='المستلم')
    subject = models.CharField(max_length=255, verbose_name='الموضوع')
    body = models.TextField(verbose_name='المحتوى')
    message_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='عام', verbose_name='نوع الرسالة')
    is_read = models.BooleanField(default=False, verbose_name='مقروءة')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'رسالة داخلية'
        verbose_name_plural = 'الرسائل الداخلية'
        ordering = ['-created_at']

    def __str__(self):
        return f"من {self.sender.get_short_name()} إلى {self.recipient.get_short_name()}: {self.subject}"
