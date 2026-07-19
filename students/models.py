from django.db import models
from django.utils.text import slugify


class Contact(models.Model):
    """بيانات التواصل"""
    first_name = models.CharField(max_length=100, db_index=True, verbose_name='الاسم الأول')
    second_name = models.CharField(max_length=100, blank=True, verbose_name='الاسم الثاني')
    third_name = models.CharField(max_length=100, blank=True, verbose_name='الاسم الثالث')
    forth_name = models.CharField(max_length=100, db_index=True, verbose_name='الاسم الرابع')
    
    address = models.TextField(blank=True, verbose_name='العنوان')
    mobile = models.CharField(max_length=20, blank=True, db_index=True, verbose_name='المحمول')
    phone = models.CharField(max_length=20, blank=True, verbose_name='التليفون')
    
    nationality = models.CharField(max_length=100, blank=True, verbose_name='الجنسية')
    identity_number = models.CharField(max_length=50, blank=True, verbose_name='رقم الهوية')
    identity_location = models.CharField(max_length=255, blank=True, verbose_name='مكان إصدار الهوية')
    identity_start_date = models.DateField(null=True, blank=True, verbose_name='تاريخ إصدار الهوية')
    
    birth_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الميلاد')
    birth_location = models.CharField(max_length=255, blank=True, verbose_name='مكان الميلاد')
    qualification = models.CharField(max_length=255, blank=True, verbose_name='المؤهل')
    
    photo = models.ImageField(upload_to='contact_photos/', blank=True, verbose_name='الصورة')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'جهة اتصال'
        verbose_name_plural = 'جهات الاتصال'
        ordering = ['-created_at']

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        names = [self.first_name, self.second_name, self.third_name, self.forth_name]
        return ' '.join(filter(None, names))

    def get_short_name(self):
        return f"{self.first_name} {self.forth_name}".strip()


class Student(models.Model):
    """الطالب"""
    LEVEL_CHOICES = [
        ('مبتدئ', 'مبتدئ'),
        ('متوسط', 'متوسط'),
        ('متقدم', 'متقدم'),
    ]
    CONTACT_CHOICES = [
        ('email', 'البريد الإلكتروني'),
        ('whatsapp', 'واتساب'),
        ('app', 'إشعار التطبيق'),
    ]
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, verbose_name='الرابط المختصر')
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, related_name='student', verbose_name='جهة الاتصال')
    branch = models.ForeignKey('core.Branch', on_delete=models.PROTECT, related_name='students', verbose_name='الفرع')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='مبتدئ', db_index=True, verbose_name='المستوى')
    preferred_contact = models.CharField(max_length=20, choices=CONTACT_CHOICES, default='whatsapp', db_index=True, verbose_name='طريقة التواصل المفضلة')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'طالب'
        verbose_name_plural = 'الطلاب'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug and self.contact_id:
            base = slugify(self.contact.get_full_name(), allow_unicode=True)
            slug = base
            counter = 1
            while Student.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.contact.get_full_name()

    def get_full_name(self):
        return self.contact.get_full_name()

    def get_mobile(self):
        return self.contact.mobile
