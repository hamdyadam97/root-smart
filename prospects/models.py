from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Prospect(models.Model):
    """المستفسر / جهة الطلب"""

    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('contacted', 'تم التواصل'),
        ('no_answer', 'لم يتم الرد'),
        ('not_interested', 'غير مهتم'),
        ('interested', 'مهتم'),
    ]

    COMMUNICATION_METHOD_CHOICES = [
        ('phone', 'تلفون'),
        ('whatsapp', 'واتساب'),
        ('email', 'بريد إلكتروني'),
        ('visit', 'زيارة'),
        ('other', 'أخرى'),
    ]

    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    branch = models.ForeignKey('core.Branch', on_delete=models.PROTECT, related_name='prospects', verbose_name='الفرع')

    # بيانات المستفسر
    name = models.CharField(max_length=255, verbose_name='الاسم')
    mobile = models.CharField(max_length=20, blank=True, verbose_name='رقم الجوال')

    # التخصص المهتم به
    master = models.ForeignKey('courses.Master', on_delete=models.SET_NULL, null=True, blank=True, related_name='prospects', verbose_name='التخصص')

    # بيانات إضافية
    workplace = models.CharField(max_length=255, blank=True, verbose_name='جهة العمل')
    ministry = models.CharField(max_length=255, blank=True, verbose_name='الوزارة / المؤسسة')
    governorate = models.CharField(max_length=255, blank=True, verbose_name='المحافظة')
    communication_method = models.CharField(max_length=20, choices=COMMUNICATION_METHOD_CHOICES, default='phone', verbose_name='وسيلة التواصل')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')

    # بيانات التواصل
    contact_date = models.DateField(default=timezone.now, verbose_name='تاريخ التواصل')
    contacted_by = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='prospects_contacted', verbose_name='الموظف الذي قام بالتواصل')

    # حالة التواصل
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', db_index=True, verbose_name='حالة التواصل')

    # تحويل إلى طالب
    student = models.OneToOneField('students.Student', on_delete=models.PROTECT, null=True, blank=True, related_name='prospect', verbose_name='الطالب')
    converted_at = models.DateTimeField(null=True, blank=True, verbose_name='تاريخ التحويل')
    converted_by = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='prospects_converted', verbose_name='المحول إلى طالب')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'مستفسر'
        verbose_name_plural = 'المستفسرون'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            while Prospect.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_status_display_class(self):
        mapping = {
            'new': 'bg-secondary',
            'contacted': 'bg-info',
            'no_answer': 'bg-warning',
            'not_interested': 'bg-dark',
            'interested': 'bg-success',
        }
        return mapping.get(self.status, 'bg-secondary')


class ProspectOffer(models.Model):
    """عرض مُرسل لمستفسر"""

    STATUS_CHOICES = [
        ('waiting', 'بانتظار الرد'),
        ('accepted', 'تم قبول العرض'),
        ('rejected', 'تم رفض العرض'),
    ]

    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name='offers', verbose_name='المستفسر')
    branch = models.ForeignKey('core.Branch', on_delete=models.PROTECT, related_name='prospect_offers', verbose_name='الفرع')

    title = models.CharField(max_length=255, verbose_name='اسم العرض أو البرنامج')
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True, related_name='prospect_offers', verbose_name='الدورة')
    content = models.TextField(blank=True, verbose_name='محتوى العرض')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='السعر')

    sent_by = models.ForeignKey('accounts.Person', on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_prospect_offers', verbose_name='الموظف الذي أرسل العرض')
    sent_at = models.DateTimeField(default=timezone.now, verbose_name='تاريخ إرسال العرض')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting', db_index=True, verbose_name='حالة العرض')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'عرض مستفسر'
        verbose_name_plural = 'عروض المستفسرين'
        ordering = ['-sent_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True)
            slug = base_slug
            counter = 1
            while ProspectOffer.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_status_display_class(self):
        mapping = {
            'waiting': 'bg-warning',
            'accepted': 'bg-success',
            'rejected': 'bg-danger',
        }
        return mapping.get(self.status, 'bg-secondary')
