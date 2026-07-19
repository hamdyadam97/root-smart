from django.db import models


class KnowledgeSnippet(models.Model):
    """مقاطع المعرفة عن المشروع"""
    CATEGORY_CHOICES = [
        ('general', 'عام'),
        ('architecture', 'هيكل المشروع'),
        ('models', 'الموديلات'),
        ('views', 'الViews'),
        ('urls', 'الروابط'),
        ('setup', 'التشغيل والإعداد'),
        ('accounts', 'المستخدمين والصلاحيات'),
        ('students', 'الطلاب'),
        ('courses', 'الدورات'),
        ('registrations', 'التسجيلات'),
        ('finance', 'المالية'),
        ('offers', 'العروض'),
        ('messaging', 'المراسلة'),
        ('notifications', 'الإشعارات'),
        ('reports', 'التقارير'),
        ('frontend', 'الواجهة الأمامية'),
        ('howto', 'إجراءات العمل'),
    ]

    title = models.CharField(max_length=255, verbose_name='العنوان')
    content = models.TextField(verbose_name='المحتوى')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='general', verbose_name='التصنيف')
    source_file = models.CharField(max_length=255, blank=True, verbose_name='ملف المصدر')
    keywords = models.TextField(blank=True, verbose_name='الكلمات المفتاحية')
    order = models.PositiveIntegerField(default=0, verbose_name='الترتيب')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مقطع معرفة'
        verbose_name_plural = 'مقاطع المعرفة'
        ordering = ['category', 'order', 'id']

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"


class ChatSession(models.Model):
    """جلسة شات"""
    session_id = models.CharField(max_length=100, unique=True, db_index=True, verbose_name='معرف الجلسة')
    title = models.CharField(max_length=255, blank=True, verbose_name='العنوان')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'جلسة شات'
        verbose_name_plural = 'جلسات الشات'
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.session_id[:8]


class ChatMessage(models.Model):
    """رسالة شات"""
    ROLE_CHOICES = [
        ('user', 'المستخدم'),
        ('assistant', 'المساعد'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages', verbose_name='الجلسة')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='الدور')
    content = models.TextField(verbose_name='المحتوى')
    sources = models.JSONField(default=list, blank=True, verbose_name='المصادر')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'رسالة شات'
        verbose_name_plural = 'رسائل الشات'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}"
